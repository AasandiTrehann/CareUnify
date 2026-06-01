import socket
import time

# HL7 MLLP standard framing bytes
START_BLOCK = b'\x0b'
END_BLOCK = b'\x1c\x0d'

# Port of our running HL7 Listener
HOST = "127.0.0.1"
PORT = 2575

def send_hl7_message(msg_text: str):
    # Wrap message in MLLP frame
    mllp_msg = START_BLOCK + msg_text.encode("utf-8") + END_BLOCK
    
    print(f"[*] Connecting to HL7 MLLP listener at {HOST}:{PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            print("[+] Connected. Sending HL7 message...")
            sock.sendall(mllp_msg)
            print("[+] Message sent successfully.")
            
            # Brief pause to receive any MLLP ACK response if needed
            time.sleep(0.5)
    except Exception as e:
        print(f"[-] Failed to transmit message: {e}")

if __name__ == "__main__":
    # Sample HL7 v2 ADT/ORU message
    # Patient name: John Doe (will match the existing Golden Record)
    # New HL7 address: 456 Elm St, Springfield, IL (will update the Golden Record via survivorship!)
    sample_message = (
        "MSH|^~\\&|EPIC|CLINIC_A|||20260529230000||ADT^A08|MSG001|P|2.3\r"
        "PID|||999-12-3456^^^US-SSN||Doe^John^Alexander||19800515|M|||456 Elm St^^Springfield^IL^62701||555-0192\r"
        "PV1||O|AMB||||||||||||||||||||||||||||||||||||||||20260529\r"
        "OBX|1|NM|2093-3^Cholesterol^LN||225|mg/dL||N|||F\r"
    )
    
    send_hl7_message(sample_message)
