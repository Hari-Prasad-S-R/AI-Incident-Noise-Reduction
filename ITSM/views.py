import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
import pandas as pd
import requests
from django.core.paginator import Paginator
from ITSM.forms import IncidentForm
from ITSM.models import Incident
from django.views.decorators.csrf import csrf_exempt
from ITSM.constants import API_BASE_URL,BASE_FOLDER_PATH,APP_USER_NAME, APP_PASSWORD, DYNAMIC_THRESHOLD_PATH,CPU_UTIL_GET_URL, METRICS_GET_URL

# Create your views here.
auth = requests.auth.HTTPBasicAuth(APP_USER_NAME, APP_PASSWORD)
# List incidents with pagination
def incident_list(request):
    incidents = Incident.objects.all()  # Fetch all incidents
    
    paginator = Paginator(incidents, 10)  # Show 10 incidents per page
    page_number = request.GET.get('page')  # Get page number from the URL
    page_obj = paginator.get_page(page_number)  # Get the paginated data
    
    return render(request, 'incident_list.html', {'page_obj': page_obj})

# Create an incident
def incident_create(request):
    if request.method == 'POST':
        form = IncidentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('incident_list')
    else:
        form = IncidentForm()
    return render(request, 'incident_form.html', {'form': form, 'form_title': 'Create Incident'})

# Edit an incident
def incident_edit(request, incident_id):
    incident = get_object_or_404(Incident, pk=incident_id)
    if request.method == 'POST':
        form = IncidentForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            return redirect('incident_list')  # Redirect to the incident list view
    else:
        form = IncidentForm(instance=incident)
    return render(request, 'incident_form.html', {'form': form, 'form_title': 'Edit Incident'})

# Delete an incident
def incident_delete(request, incident_id):
    incident = get_object_or_404(Incident, pk=incident_id)
    if request.method == 'POST':  # Confirm deletion
        incident.delete()
        print("deleted")
        return redirect('incident_list')  # Redirect to the incident list view
    return redirect('incident_list')

def get_dynamic_threshold(timestamp):
    try:
        forecast_data = pd.read_csv(DYNAMIC_THRESHOLD_PATH)
        # Target timestamp
        target_timestamp = pd.Timestamp(timestamp).round(freq='5min').tz_localize(None)
        forecast_data['ds'] = pd.to_datetime(forecast_data['ds'], format="mixed").dt.tz_localize(None)
        # Find the nearest timestamp
        nearest_row = forecast_data.loc[(forecast_data['ds'] - target_timestamp).abs().idxmin()]
        return float(nearest_row['yhat_upper'])
    except Exception as exc:
        return None

def get_metric_value(metrics_text, metric_name):
    """Extracts the value of a given metric from Prometheus-style metrics."""
    for line in metrics_text.splitlines():
        if line.startswith(metric_name):
            _, value = line.split()
            return float(value)
    return None

def handle_mem_alert(metrics):
    total_memory = get_metric_value(metrics, "windows_memory_physical_total_bytes")
    available_memory = get_metric_value(metrics, "windows_memory_available_bytes")

    if total_memory and available_memory:
        # Calculate memory usage percentage
        alert_value = 1 - (available_memory / total_memory)
        print(f"Memory Usage: {alert_value:.2%}")  # Display as a percentage
        return alert_value
    else:
        print("Error: Could not find required metrics in response.")
        return 100.00
    
def handle_cpu_alert():
    data = requests.get(CPU_UTIL_GET_URL).json()
    return float(data.result.value[1])

@csrf_exempt
def webhook_create(request):
    print(request.body)
    json_val = json.loads(request.body.decode("utf-8"))
    for alert in json_val['alerts']:
        #OLD_FLOW

        incident = Incident(title="OLD_FLOW:"+alert['labels']['alertname']+f"recieved from {alert['generatorURL']}", description = alert['annotations']['description'], status = "Open")
        incident.save()

        #NEW_FLOW
        alert_threshold=80
        dyn_threshold = get_dynamic_threshold(alert['startsAt'])
        metrics = requests.get(METRICS_GET_URL).text
        alert_value = None

        if alert['labels']['alertname'] == "HighMemoryUsage":
            alert_value = handle_mem_alert(metrics)
        elif alert['labels']['alertname'] == "HighCPUUsage":
            alert_value = handle_mem_alert()
        print(f"Dynamic Threshold: {dyn_threshold}")     
        if dyn_threshold > alert_threshold and alert_value > dyn_threshold:
            incident = Incident(title="NEW_FLOW:"+alert['labels']['alertname']+f"recieved from {alert['generatorURL']}", description = alert['annotations']['description'] + f"with curent utilisation @ {alert_value}", status = "Open")
            incident.save()
        else:
            print("No Incident requiredas this is a expected scenrio")
        return JsonResponse({"status":"Data Processsed Successfully"})
