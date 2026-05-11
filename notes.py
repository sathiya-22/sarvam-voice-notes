"""Sarvam Voice Notes — record, transcribe, search in Indian languages."""
import os, io, sqlite3, datetime
import numpy as np, sounddevice as sd, soundfile as sf
from dotenv import load_dotenv
from sarvamai import SarvamAI
from rich.console import Console
from rich.table import Table

load_dotenv()
console=Console()
client=SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])
SR=16000; DB="notes.db"

def init():
    c=sqlite3.connect(DB); c.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY,created TEXT,lang TEXT,transcript TEXT,translation TEXT)"); c.commit(); return c

def record(sec=8):
    console.print("[red]● Recording...[/red]")
    a=sd.rec(int(sec*SR),samplerate=SR,channels=1,dtype="float32"); sd.wait(); return a.flatten()

def transcribe(audio, lang):
    buf=io.BytesIO(); sf.write(buf,audio,SR,format="WAV"); buf.seek(0)
    t=client.speech_to_text.transcribe(file=buf,model="saaras:v3",language_code=lang).transcript
    tr=t if lang=="en-IN" else client.text.translate(input=t,source_language_code=lang,target_language_code="en-IN").translated_text
    return t,tr

def main():
    conn=init(); console.print("[bold]Sarvam Voice Notes[/bold] — [r]ecord [s]earch [l]ist [q]uit")
    while True:
        cmd=input("\n> ").strip().lower()
        if cmd=="q": break
        elif cmd=="r":
            lang=input("Language (hi-IN/ta-IN/en-IN) [hi-IN]: ").strip() or "hi-IN"
            audio=record(); t,tr=transcribe(audio,lang)
            console.print(f"[cyan]Transcript:[/cyan] {t}"); console.print(f"[green]Translation:[/green] {tr}")
            conn.execute("INSERT INTO notes VALUES (NULL,?,?,?,?)",(str(datetime.datetime.now()),lang,t,tr)); conn.commit(); console.print("[green]Saved![/green]")
        elif cmd=="s":
            q=input("Search: ")
            rows=conn.execute("SELECT id,created,lang,translation FROM notes WHERE transcript LIKE ? OR translation LIKE ?",  (f"%{q}%",f"%{q}%")).fetchall()
            tb=Table(); [tb.add_column(c) for c in ["ID","Created","Lang","Translation"]]
            for r in rows: tb.add_row(*[str(x) for x in r])
            console.print(tb)
        elif cmd=="l":
            rows=conn.execute("SELECT id,created,lang,translation FROM notes ORDER BY id DESC LIMIT 20").fetchall()
            tb=Table(); [tb.add_column(c) for c in ["ID","Created","Lang","Translation"]]
            for r in rows: tb.add_row(*[str(x) for x in r])
            console.print(tb)

if __name__=="__main__": main()
