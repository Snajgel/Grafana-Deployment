#!/bin/bash

pushgateway_endpoint="http://127.0.0.1:9091"
job_name="jobname"

# Get the IP address of eth0
ip_address=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

# Generate a temporary file to store the metrics
temp_file=$(mktemp)

# Format the metrics output in Prometheus format (IP as a label)
cat <<EOF > "$temp_file"
pushgateway_ip_metric{ip_address="$ip_address"} 1
EOF

# Push the metrics to Pushgateway
curl --data-binary "@$temp_file" "$pushgateway_endpoint/metrics/job/$job_name"

# Clean up the temporary file
rm "$temp_file"