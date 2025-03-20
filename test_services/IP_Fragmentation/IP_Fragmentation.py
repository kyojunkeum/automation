import conf
from scapy.all import IP, UDP, Raw, Ether, send, conf

# 대상 IP 설정
dlp_ip = "172.16.150.187"  # DLP 서버 IP
client_ip = "172.16.150.132"  # 클라이언트 IP

# MTU보다 큰 페이로드를 사용하여 강제 Fragmentation 유도
payload = b"A" * 3000  # 3000 바이트의 데이터

# 첫 번째 조각 (Fragment Offset 0)
frag1 = IP(src=client_ip, dst=dlp_ip, id=12345, flags="MF", frag=0) / UDP(dport=53) / Raw(load=payload[:1400])

# 두 번째 조각 (Fragment Offset 1400 / 8 = 175)
frag2 = IP(src=client_ip, dst=dlp_ip, id=12345, flags="MF", frag=175) / Raw(load=payload[1400:2800])

# 세 번째 조각 (Fragment Offset 2800 / 8 = 350, 마지막 조각이므로 MF 플래그 없음)
frag3 = IP(src=client_ip, dst=dlp_ip, id=12345, frag=350) / Raw(load=payload[2800:])

# 패킷 전송
send([frag1, frag2, frag3])

print("IP_Fragmentation 패킷을 전송했습니다.")
