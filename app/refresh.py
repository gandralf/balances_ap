from datetime import datetime
import paramiko
import os
from typing import TypedDict, List, Dict
import logging
import pika
import json

class AccountBalance(TypedDict):
    account_id: str
    balances: Dict[str, float]

def last_file_name() -> str:
    date = datetime.now().strftime('%m_%d_%Y')
    timestamp_str = datetime.now().strftime('%Y-%m-%d 00:00+00:00')
    return timestamp_str, f'AccountBalances_{date}.csv'

def download_last_file_from_sftp() -> str:
    timestamp_str, file_name = last_file_name()
    
    host = os.getenv('SFTP_HOST') or os.getenv('SFTP_URL')  # Check both env vars
    username = os.getenv('SFTP_USERNAME')
    password = os.getenv('SFTP_PASSWORD')
    
    logging.info(f"Connecting to SFTP server: {host}, username: {username}")
    
    # Create a transport directly to the SFTP server
    transport = paramiko.Transport((host, 22))
    try:
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        local_path = os.path.join(os.getcwd(), file_name)
        sftp.chdir('reports')
        sftp.get(file_name, local_path)
        logging.info(f"Successfully downloaded file to {local_path}")
        
        return timestamp_str, local_path
    except Exception as e:
        logging.error(f"SFTP error: {str(e)}")
        raise
    finally:
        transport.close()


def load_csv_file(csv_path: str) -> List[AccountBalance]:
    ignore_accounts = os.getenv('IGNORE_ACCOUNTS', '').split(',')
    with open(csv_path, 'r') as f:
        content = f.read()
        lines = [line.replace('"', '').split(',') for line in content.splitlines()]
        header = lines[0]
        result = []
        for line in lines[1:]:
            account_id = line[0]
            if account_id in ignore_accounts:
                continue
            balances = {}
            for i, asset_spec in enumerate(header[1:-1]):
                balance = float(line[i + 1])
                balances[asset_spec] = balance
            result.append(AccountBalance(account_id=account_id, balances=balances))
            
        return result


def process_csv_content(content: List[AccountBalance]) -> Dict[str, float]:
    summary = {}
    for account in content:
        for asset_spec, balance in account['balances'].items():
            if asset_spec not in summary:
                summary[asset_spec] = 0
            summary[asset_spec] += balance

    return summary


def send_to_rabbitmq(date: str, summary: Dict[str, float]) -> None:
    rabbitmq_url: Optional[str] = os.getenv('RABBITMQ_URL')  # should be set in .env or environment
    if rabbitmq_url is None:
        raise ValueError("RABBITMQ_URL environment variable not set")
        
    exchange_name: str = "big-data"                # or "assets" — adjust as you prefer
    routing_key: str = "insert"                    # as requested

    connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
    channel = connection.channel()

    # Declare the exchange (topic, durable)
    channel.exchange_declare(exchange=exchange_name, exchange_type='direct', durable=True)

    data = []
    for asset_spec, balance in summary.items():
        _, coin = asset_spec.split('-')
        data.append({
            'coin': coin,
            'amount': balance,
            'date': date
        })
    
    payload = {
        'metadata': {
            'type': 'account_balances'
        },
        'data': data
    }
    channel.basic_publish(exchange=exchange_name, routing_key=routing_key, body=json.dumps(payload))
    connection.close()

def refresh_balances():
    date_str, csv_path = download_last_file_from_sftp()
    content = load_csv_file(csv_path)
    summary = process_csv_content(content)
    send_to_rabbitmq(date_str, summary)
