#!/usr/bin/env python3

import socket
import requests
import datetime
import speedtest
import subprocess
import psutil
import smtplib
from pathlib import Path
from tcp_latency import measure_latency
from email.message import EmailMessage

# Terminal formatting
BOLD_CYAN = '\033[1;96m'
BOLD_MAGENTA = '\033[1;95m'
RESET = '\033[0m'
output_lines = []

def log(msg, level=None):
    if level == "OK":
        color = '\033[92m'
        tag = "[OK]"
    elif level == "FAIL":
        color = '\033[91m'
        tag = "[FAIL]"
    else:
        color = '\033[0m'
        tag = ""
    line = f"{tag} {msg}" if tag else msg
    print(f"{color}{line}{RESET}")
    output_lines.append(line)

def print_header(title):
    border = f"{BOLD_MAGENTA}{'#' * (len(title) + 10)}{RESET}"
    print(border)
    print(f"{BOLD_CYAN}{title}{RESET}")
    print(border)

def send_email_report(html_path, subject, sender_email, recipient_email, smtp_server, smtp_port, smtp_user, smtp_password):
    try:
        with open(html_path, 'r') as f:
            html_content = f.read()

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg.set_content("Your network diagnostics report is attached as HTML.", subtype='plain')
        msg.add_alternative(html_content, subtype='html')

        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)

        log("Email sent successfully.", "OK")
    except Exception as e:
        log(f"Failed to send email: {e}", "FAIL")

def main():
    hostname = socket.gethostname()
    timestamp = datetime.datetime.now().strftime("%d%m%y_%H-%M")
    report_dir = Path("/home/monadmin")
    report_dir.mkdir(parents=True, exist_ok=True)
    txt_path = report_dir / f"{hostname}_BRS_GENERAL_transcript_{timestamp}.txt"
    html_path = report_dir / f"{hostname}_BRS_GENERAL_transcript_{timestamp}.html"

    print_header("BRS SERVICE GENERAL")
    log("Version 15")
    log("Property of Alantra")

    print_header("LOCAL NETWORK INTERFACES")
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                log(f"Interface: {iface} - IP: {addr.address} - Netmask: {addr.netmask}")

    print_header("SPEED TEST RESULTS")
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download() / 1_000_000
        upload = st.upload() / 1_000_000
        ping_result = st.results.ping
        log(f"Download: {download:.2f} Mbps", "OK")
        log(f"Upload: {upload:.2f} Mbps", "OK")
        log(f"Ping: {ping_result:.2f} ms", "OK")
    except Exception as e:
        log(f"Speedtest failed: {e}", "FAIL")

    print_header("GEOLOCATION AND PUBLIC IP")
    try:
        ip = requests.get("https://api.ipify.org").text.strip()
        geo = requests.get(f"http://ip-api.com/json/{ip}").json()
        log(f"Public IP: {ip}")
        for key in ['country', 'regionName', 'city', 'zip', 'lat', 'lon', 'timezone', 'isp']:
            log(f"{key.title()}: {geo.get(key)}")
    except Exception as e:
        log(f"Geolocation lookup failed: {e}", "FAIL")

    print_header("SERVICE CONNECTIVITY TEST")
    services = {
        "ALNAZPRODEUWEDC.NMASUNO.COM": [389, 636, 445],
        "ALNAZPRODC02.NMASUNO.COM": [389, 636, 445],
        "ALNADAZ03.NMASUNO.COM": [389, 636, 445],
        "ALNPRODSQLGS02.NMASUNO.COM": [1433, 1435],
        "ALNPRODPRINTAZ0.NMASUNO.COM": [445],
        "ALNPRINTAZ02.NMASUNO.COM": [445],
        "ALNAZ1.NMASUNO.COM": [445], "ALNAZ2.NMASUNO.COM": [445], "ALNAZ3.NMASUNO.COM": [445],
        "ALNAZ4.NMASUNO.COM": [445], "ALNAZ5.NMASUNO.COM": [445], "ALNAZ7.NMASUNO.COM": [445],
        "ALANTRA2018.NMASUNO.COM": [445],
        "nmasuno.com": [389, 636, 445],
        "adam.alantra.com": [4438],
        "10.174.36.4": [4441],
        "ALNAPPZA02.NMASUNO.COM": [8444, 8081],
        "adsi.alantra.com": [451, 453]
    }

    for host, ports in services.items():
        for port in ports:
            try:
                socket.create_connection((host, port), timeout=3).close()
                log(f"{host}:{port} CONNECTION OK", "OK")
            except Exception as e:
                log(f"{host}:{port} CONNECTION KO ({e})", "FAIL")

    print_header("LATENCY TESTS")
    total = sum(len(ports) for ports in services.values())
    count = 0

    for host, ports in services.items():
        for port in ports:
            try:
                rtts = measure_latency(host=host, port=port, runs=3, timeout=2.0)
                valid_rtts = [r for r in rtts if r is not None]
                count += 1
                percent = int((count / total) * 100)

                if valid_rtts:
                    avg_rtt = sum(valid_rtts) / len(valid_rtts)
                    log(f"{host}:{port} - Avg TCP Latency: {avg_rtt:.2f} ms", "OK")
                else:
                    log(f"{host}:{port} - No TCP response", "FAIL")

                print(f"Progress: {percent}%")
            except Exception as e:
                log(f"{host}:{port} - TCP latency check failed: {e}", "FAIL")

    print_header("TEST URL CONNECTIONS")
    urls = [
        "https://anisa.alantra.com", "https://enma.alantra.com", "https://vdr.alantra.com",
        "https://www.alantra.com", "https://www.google.com",
        "https://adsi.alantra.com:451", "https://adsi.alantra.com:453",
        "https://adaudit.alantra.com:8081", "https://adaudit.alantra.com:8444"
    ]
    for url in urls:
        try:
            result = subprocess.run(
                ['curl', '-L', '--insecure', '-A', 'Mozilla/5.0',
                 '-o', '/dev/null', '-s', '-w', '%{http_code}', url],
                capture_output=True, text=True, timeout=10
            )
            status = result.stdout.strip()
            if status == "000":
                log(f"{url} NO RESPONSE (Status: 000)", "FAIL")
            elif status.startswith("2") or status.startswith("3") or status in {"401", "403"}:
                log(f"{url} CONNECTION OK (Status: {status})", "OK")
            elif status == "404":
                log(f"{url} REACHABLE (Status: 404 Not Found)")
            else:
                log(f"{url} CONNECTION KO (Status: {status})", "FAIL")
        except subprocess.TimeoutExpired:
            log(f"{url} TIMEOUT", "FAIL")
        except Exception as e:
            log(f"{url} CURL ERROR: {e}", "FAIL")

    # Save .txt
    with open(txt_path, "w") as f:
        for line in output_lines:
            f.write(line + "\n")

    # Save .html
    html_head = """<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<title>Network Report</title>
<style>
body { font-family: Arial; background: #f9f9f9; padding: 20px; }
.OK { color: green; }
.FAIL { color: red; }
pre { background: #eee; padding: 10px; border-radius: 5px; }
</style></head><body>
<h1>Network Diagnostics Report</h1><pre>
"""
    html_body = "\n".join(
        f'<span class="{line.split("]")[0][1:].strip()}">{line}</span>' if line.startswith("[") else line
        for line in output_lines
    )
    html_footer = "</pre></body></html>"

    with open(html_path, "w") as f:
        f.write(html_head + html_body + html_footer)

    log(f"Report generated: {html_path}")

    # Send email via Outlook/Office365 (STARTTLS)
    send_email_report(
        html_path=html_path,
        subject=f"Network Report from Athens 2",
        sender_email="enma.monitoring@alantra.com",
        recipient_email="AlertasZabbix@alantra.com",
        smtp_server="smtp.office365.com",
        smtp_port=587,
        smtp_user="enma.monitoring@alantra.com",
        smtp_password="Vat35284"
    )

if __name__ == "__main__":
    main()
