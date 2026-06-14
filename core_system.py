import time
import base64
import os
import numpy as np
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from sklearn.ensemble import IsolationForest


class AIAnyalyzer:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        normal_behavior = [
            [2.5, 50], [3.0, 60], [1.8, 45], [4.0, 70], [2.2, 55],
            [3.5, 65], [1.9, 40], [2.8, 52], [3.1, 58], [2.6, 48]
        ]
        self.model.fit(normal_behavior)

    def analyze_behavior(self, time_diff, data_size):
        sample = np.array([[time_diff, data_size]])
        prediction = self.model.predict(sample)
        return "ATTACK" if prediction[0] == -1 else "NORMAL"


class AIAdaptiveSecuritySystem:
    def __init__(self):
        self.secret_key = os.urandom(32)
        self.ai_engine = AIAnyalyzer()
        self.last_request_time = time.time()
        self.security_level = "NORMAL"

    def rotate_key(self):
        self.secret_key = os.urandom(32)

    def process_request(self, data: str):
        current_time = time.time()
        time_diff = current_time - self.last_request_time
        data_size = len(data.encode())
        self.last_request_time = current_time

        verdict = self.ai_engine.analyze_behavior(time_diff, data_size)
        self.security_level = verdict

        is_delayed = False
        if verdict == "ATTACK":
            self.rotate_key()
            is_delayed = True

        # التشفير باستخدام AES-GCM
        iv = os.urandom(12)
        encryptor = Cipher(
            algorithms.AES(self.secret_key),
            modes.GCM(iv),
            backend=default_backend()
        ).encryptor()

        ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
        final_cipher = base64.b64encode(iv + encryptor.tag + ciphertext).decode()

        return {
            "cipher_text": final_cipher,
            "status": verdict,
            "time_diff": round(time_diff, 3),
            "data_size": data_size,
            "key_rotated": is_delayed,
            "raw_data": data,
            "current_iv": iv,
            "current_tag": encryptor.tag,
            "current_key": self.secret_key
        }

    def decrypt_data(self, cipher_text_b64, key, iv, tag):
        """فك تشفير البيانات المعالجة"""
        try:
            raw_cipher = base64.b64decode(cipher_text_b64.encode())
            actual_ciphertext = raw_cipher[28:]

            decryptor = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=default_backend()
            ).decryptor()

            decrypted_bytes = decryptor.update(actual_ciphertext) + decryptor.finalize()
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            return f"❌ فشل فك التشفير (تم تغيير المفتاح بسبب الهجوم!): {str(e)}"