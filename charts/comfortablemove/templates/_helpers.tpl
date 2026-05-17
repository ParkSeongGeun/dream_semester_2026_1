{{- define "comfortablemove.name" -}}
{{- .Chart.Name }}
{{- end }}

{{- define "comfortablemove.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "comfortablemove.labels" -}}
app.kubernetes.io/name: {{ include "comfortablemove.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "comfortablemove.selectorLabels" -}}
app.kubernetes.io/name: {{ include "comfortablemove.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
