{{/* Common labels applied to every resource in this chart. */}}
{{- define "protopane.labels" -}}
app.kubernetes.io/name: protopane
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: protopane
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{/* Subset suitable for matchLabels / selector. */}}
{{- define "protopane.selectorLabels" -}}
app.kubernetes.io/name: protopane
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
