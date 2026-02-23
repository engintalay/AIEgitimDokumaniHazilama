✅ COMPLETED:

* ✅ Admin sistemde online olan kullanıcıları görebiliyor. (Status: 🟢 Online / ⏱️ Idle / 🔴 Offline)
  - Last activity timestamp ile otomatik status güncelleniyor (5 min heartbeat)
  - Admin panel users listesi 30 saniyede bir güncelleniyor
  
* ✅ Admin-to-user chat: Support ticket sistemi üzerinden mesajlaşma
  - "💬 Mesaj Gönder" butonuyla belirlenen kullanıcıya direkt mesaj gönder
  - Existing Report/ticket system kullanıyor (no extra code)
  
* ✅ LM Studio processing bilgileri gösteriliyor
  - Model adı, temperature, prompt/completion tokens
  - Response time ve tokens/sec hızı
  - Sistem message (collapsible details)
  - ⚙️ butonuyla chat mesajlarında processing info modal açılıyor

DB Migration: ✅ COMPLETE
- last_activity added to user table
- model_name, temperature added to message table
- No data loss, 4 users + 84 messages preserved
