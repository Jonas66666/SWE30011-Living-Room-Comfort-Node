#!/usr/bin/env python3
"""
Complete AWS IoT Core Diagnostic Script
Tests every possible issue
"""

import os
import sys
import ssl
import socket

# ==================== CHECK FILES ====================
print("=" * 60)
print("STEP 1: CHECKING CERTIFICATE FILES")
print("=" * 60)

CERT_FILE = "/home/pi/certs/LivingRoomPi.cert.pem"
KEY_FILE = "/home/pi/certs/LivingRoomPi.private.key"
ROOT_CA_FILE = "/home/pi/certs/AmazonRootCA1.pem"

for file_path in [CERT_FILE, KEY_FILE, ROOT_CA_FILE]:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ FOUND: {file_path} ({size} bytes)")
        
        # Check first line of each file
        with open(file_path, 'r') as f:
            first_line = f.readline().strip()
            print(f"   First line: {first_line[:50]}...")
    else:
        print(f"❌ MISSING: {file_path}")

# ==================== CHECK FILE PERMISSIONS ====================
print("\n" + "=" * 60)
print("STEP 2: CHECKING FILE PERMISSIONS")
print("=" * 60)

for file_path in [CERT_FILE, KEY_FILE]:
    import stat
    mode = os.stat(file_path).st_mode
    print(f"{file_path}: {oct(mode)[-3:]}")

# ==================== CHECK NETWORK ====================
print("\n" + "=" * 60)
print("STEP 3: CHECKING NETWORK CONNECTIVITY")
print("=" * 60)

ENDPOINT = "a23t40n3bsphuc-ats.iot.us-east-1.amazonaws.com"
PORT = 8883

print(f"Pinging {ENDPOINT}...")
response = os.system(f"ping -c 1 {ENDPOINT} > /dev/null 2>&1")
if response == 0:
    print("✅ Ping successful")
else:
    print("❌ Ping failed - Check internet connection")

print(f"\nTesting connection to {ENDPOINT}:{PORT}...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((ENDPOINT, PORT))
    if result == 0:
        print(f"✅ Port {PORT} is reachable")
    else:
        print(f"❌ Port {PORT} is NOT reachable (Error: {result})")
    sock.close()
except Exception as e:
    print(f"❌ Connection test failed: {e}")

# ==================== CHECK DATE/TIME ====================
print("\n" + "=" * 60)
print("STEP 4: CHECKING SYSTEM DATE/TIME")
print("=" * 60)

import datetime
now = datetime.datetime.now()
print(f"Current system time: {now}")
print("Make sure this is within a few minutes of actual time!")

# ==================== TRY SSL CONNECTION ====================
print("\n" + "=" * 60)
print("STEP 5: TESTING SSL HANDSHAKE")
print("=" * 60)

try:
    context = ssl.create_default_context(cafile=ROOT_CA_FILE)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((ENDPOINT, PORT))
    
    ssl_sock = context.wrap_socket(sock, server_hostname=ENDPOINT)
    print("✅ SSL Handshake SUCCESSFUL!")
    print(f"   Cipher: {ssl_sock.cipher()}")
    ssl_sock.close()
    
except ssl.SSLCertVerificationError as e:
    print(f"❌ SSL Certificate Error: {e}")
    print("   This usually means the certificate doesn't match the endpoint")
except ssl.SSLZeroReturnError as e:
    print(f"❌ SSL Connection closed unexpectedly: {e}")
except Exception as e:
    print(f"❌ SSL Error: {type(e).__name__}: {e}")

# ==================== TRY MQTT CONNECTION ====================
print("\n" + "=" * 60)
print("STEP 6: TESTING MQTT CONNECTION")
print("=" * 60)

try:
    from awscrt import mqtt
    from awsiot import mqtt_connection_builder
    
    print("Building MQTT connection...")
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT,
        cert_filepath=CERT_FILE,
        pri_key_filepath=KEY_FILE,
        ca_filepath=ROOT_CA_FILE,
        client_id="LivingRoomPi",
        clean_session=True,
        keep_alive_secs=30
    )
    
    print("Attempting to connect...")
    connect_future = mqtt_connection.connect()
    result = connect_future.result(timeout=10)
    print("✅ MQTT CONNECTION SUCCESSFUL!")
    
    mqtt_connection.disconnect().result()
    print("✅ Disconnected")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("   Run: pip install awsiotsdk")
except Exception as e:
    print(f"❌ MQTT Error: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
