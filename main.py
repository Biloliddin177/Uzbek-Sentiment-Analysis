from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
import os, re, json, csv, io, asyncio
import requests
from typing import Optional
from docx import Document as DocxDocument
from googleapiclient.discovery import build as google_build
# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
from telethon.sync import TelegramClient
from telethon import functions, types
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Uzbek Sentiment API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Telegram credentials (.env dan) ───────────────────────────
TG_API_ID       = int(os.getenv("TG_API_ID", "0"))
TG_API_HASH     = os.getenv("TG_API_HASH", "")
TG_SESSION      = os.getenv("TG_SESSION", "telegram_session")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "") or os.getenv("U_API_KEY", "")

# ── Model yuklash ──────────────────────────────────────────────
MODEL_PATH = os.getenv("MODEL_PATH", "./uzbek_sentiment_model")
print(f"[INFO] Model yuklanmoqda: {MODEL_PATH}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval()

LABELS = {0: "Neutral", 1: "Positive", 2: "Negative"}

# ── Schemas ────────────────────────────────────────────────────
class TextData(BaseModel):
    text: str

class CommentAnalysisRequest(BaseModel):
    url: str
    youtube_api_key: Optional[str] = None  # None bo'lsa .env dan olinadi
    facebook_access_token: Optional[str] = None
    max_comments: int = 100

# ── Inference ─────────────────────────────────────────────────
def run_inference(text: str) -> dict:
    inputs = tokenizer(
        text, return_tensors="pt",
        truncation=True, max_length=512, padding=True
    )
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=-1)[0]
    idx = probs.argmax().item()
    return {
        "label": LABELS[idx],
        "confidence": round(probs[idx].item(), 4),
    }

def categorize_comments(comments: list) -> dict:
    categories = {"Positive": [], "Negative": [], "Neutral": []}
    for comment in comments:
        if not comment.strip():
            continue
        result = run_inference(comment)
        label = result["label"]
        categories[label].append({
            "text": comment[:200],
            "confidence": result["confidence"]
        })
    total = sum(len(v) for v in categories.values())
    return {
        "categories": categories,
        "counts": {k: len(v) for k, v in categories.items()},
        "percentages": {
            k: round(len(v) / total * 100, 1) if total else 0
            for k, v in categories.items()
        },
        "total": total,
        "top_positive": sorted(categories["Positive"], key=lambda x: -x["confidence"])[:5],
        "top_negative": sorted(categories["Negative"], key=lambda x: -x["confidence"])[:5],
    }

# ── Platform detector ──────────────────────────────────────────
def detect_platform(url: str) -> str:
    u = url.lower()
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "instagram.com" in u:
        return "instagram"
    if "t.me" in u or "telegram.me" in u:
        return "telegram"
    if "facebook.com" in u or "fb.com" in u:
        return "facebook"
    return "unknown"

# ── YouTube ────────────────────────────────────────────────────
def extract_youtube_id(url: str) -> Optional[str]:
    for p in [r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
               r"(?:shorts/)([a-zA-Z0-9_-]{11})"]:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

def fetch_youtube_comments(video_id: str, api_key: str, max_results: int = 100) -> dict:
    youtube = google_build("youtube", "v3", developerKey=api_key)
    video_resp = youtube.videos().list(part="snippet", id=video_id).execute()
    title = video_resp["items"][0]["snippet"]["title"] if video_resp.get("items") else f"Video {video_id}"
    comments = []
    next_page = None
    fetched = 0
    while fetched < max_results:
        batch = min(100, max_results - fetched)
        kwargs = dict(part="snippet", videoId=video_id,
                      maxResults=batch, textFormat="plainText", order="relevance")
        if next_page:
            kwargs["pageToken"] = next_page
        resp = youtube.commentThreads().list(**kwargs).execute()
        for item in resp.get("items", []):
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append({"text": text})
        fetched += len(resp.get("items", []))
        next_page = resp.get("nextPageToken")
        if not next_page:
            break
    if not comments:
        raise ValueError("Bu videoda izohlar topilmadi yoki izohlar yopilgan")
    texts = [c["text"] for c in comments]
    result = categorize_comments(texts)
    return {"platform": "YouTube", "title": title, "video_id": video_id,
            "fetched_comments": len(comments), **result}

# ── Selenium driver (umumiy helper) ───────────────────────────
def get_driver() -> webdriver.Chrome:
    """Headless Chrome driver yaratadi (Windows/Linux/Mac uchun universal)."""
    from webdriver_manager.chrome import ChromeDriverManager
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    # ChromeDriver: bir nechta joylarda qidiradi
    import os, sys
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "chromedriver.exe"),
        os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "chromedriver.exe"),
        os.path.join(os.getcwd(), "chromedriver.exe"),
        r"D:\Uzbek sentiment Analysis\chromedriver.exe",
    ]
    local_driver = None
    for c in candidates:
        if os.path.exists(c):
            local_driver = c
            break
    if local_driver:
        service = Service(local_driver)
        print(f"[DEBUG] ChromeDriver topildi: {local_driver}")
    else:
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            print("[DEBUG] webdriver-manager ChromeDriver yuklab oldi")
        except Exception as e:
            print(f"[DEBUG] webdriver-manager xato: {e}")
            service = Service()
    driver = webdriver.Chrome(service=service, options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver

def random_sleep(a: float = 1.5, b: float = 3.5):
    time.sleep(random.uniform(a, b))

# ── Instagram (Selenium scraping) ─────────────────────────────
def extract_instagram_shortcode(url: str) -> Optional[str]:
    m = re.search(r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else None

def fetch_instagram_comments(url: str, max_results: int = 100) -> dict:
    """
    Instagram public post/reel izohlarini Selenium + GraphQL orqali oladi.
    """
    shortcode = extract_instagram_shortcode(url)
    if not shortcode:
        raise ValueError("Instagram post/reel URL noto'g'ri. Format: instagram.com/p/... yoki /reel/...")

    # 1-usul: Instagram GraphQL API (eng ishonchli)
    comments = []
    title = f"Post {shortcode}"
    try:
        api_url = f"https://www.instagram.com/api/v1/media/{shortcode}/comments/?can_support_threading=true&permalink_enabled=false"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "X-IG-App-ID": "936619743392459",
            "X-ASBD-ID": "129477",
            "X-IG-WWW-Claim": "0",
            "Origin": "https://www.instagram.com",
            "Referer": f"https://www.instagram.com/p/{shortcode}/",
            "Accept": "*/*",
        }
        resp = requests.get(api_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("comments", []):
                txt = item.get("text", "").strip()
                if txt and len(txt) > 1:
                    comments.append(txt)
            # next cursor bilan davom etish
            cursor = data.get("next_min_id")
            while cursor and len(comments) < max_results:
                r2 = requests.get(
                    api_url + f"&min_id={cursor}",
                    headers=headers, timeout=15
                )
                if r2.status_code != 200:
                    break
                d2 = r2.json()
                for item in d2.get("comments", []):
                    txt = item.get("text", "").strip()
                    if txt and len(txt) > 1:
                        comments.append(txt)
                cursor = d2.get("next_min_id")
                time.sleep(1)
    except Exception as e:
        print(f"[DEBUG] GraphQL usul xato: {e}")

    # 2-usul: Selenium (GraphQL ishlamasa)
    if not comments:
        driver = get_driver()
        try:
            clean_url = f"https://www.instagram.com/p/{shortcode}/"
            driver.get(clean_url)
            random_sleep(3, 5)

            # Meta title olish
            try:
                meta = driver.find_element(By.XPATH, "//meta[@property='og:title']")
                title = meta.get_attribute("content")[:100] or title
            except Exception:
                pass

            # Login/cookie popup yopish
            for xpath in [
                "//button[contains(text(),'Accept') or contains(text(),'Allow')]",
                "//button[@aria-label='Close']",
            ]:
                try:
                    btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    btn.click()
                    random_sleep(1, 2)
                except TimeoutException:
                    pass

            # Sahifa to'liq yuklanishini kutish
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            random_sleep(2, 3)

            scroll_attempts = 0
            max_scrolls = max(8, max_results // 5)

            while len(comments) < max_results and scroll_attempts < max_scrolls:
                # Keng selector — barcha span[dir=auto] ichidan izoh matnlarini olish
                all_spans = driver.find_elements(By.CSS_SELECTOR, "span[dir='auto']")
                for span in all_spans:
                    txt = span.text.strip()
                    if txt and len(txt) > 2 and txt not in comments:
                        # Username va caption ni filter qilish
                        parent = span.find_elements(By.XPATH, "./ancestor::*[@role='button']")
                        if not parent:
                            comments.append(txt)

                if len(comments) >= max_results:
                    break

                # "Load more comments" tugmasi
                clicked = False
                for sel in [
                    "svg[aria-label='Load more comments']",
                    "button._abl-",
                ]:
                    try:
                        btn = driver.find_element(By.CSS_SELECTOR, sel)
                        driver.execute_script("arguments[0].click();", btn)
                        random_sleep(2, 3)
                        clicked = True
                        break
                    except NoSuchElementException:
                        pass

                if not clicked:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    random_sleep(2, 3)

                scroll_attempts += 1

        finally:
            driver.quit()

    if not comments:
        raise ValueError(
            "Izohlar topilmadi. Instagram login talab qilishi yoki "
            "post private bo'lishi mumkin. Biroz kutib qayta urining."
        )

    result = categorize_comments(comments[:max_results])
    return {
        "platform": "Instagram",
        "title": title,
        "shortcode": shortcode,
        "fetched_comments": len(comments[:max_results]),
        **result
    }

# ── Telegram (Telethon, loginsiz - faqat api_id + api_hash) ───
def extract_telegram_username(url: str) -> tuple:
    """
    t.me/username → (username, None)
    t.me/username/123 → (username, 123)
    """
    m = re.search(r"t\.me/([^/\?]+)(?:/(\d+))?", url)
    if not m:
        return None, None
    return m.group(1), int(m.group(2)) if m.group(2) else None

async def fetch_telegram_comments(url: str, max_results: int = 100) -> dict:
    if not TG_API_ID or not TG_API_HASH:
        raise ValueError(
            "Server konfiguratsiyasida TG_API_ID va TG_API_HASH yo'q. "
            ".env faylni tekshiring."
        )

    username, post_id = extract_telegram_username(url)
    if not username:
        raise ValueError("Telegram URL noto'g'ri. Format: https://t.me/username yoki https://t.me/username/123")

    comments = []
    title = username

    async with TelegramClient(TG_SESSION, TG_API_ID, TG_API_HASH) as client:
        # Kanal/guruh ma'lumotlarini olish
        try:
            entity = await client.get_entity(username)
            title = getattr(entity, "title", username)
        except Exception as e:
            raise ValueError(f"Kanal/guruh topilmadi: @{username}. Public bo'lishi kerak. ({e})")

        # Post ID ko'rsatilgan bo'lsa — o'sha postning discussion izohlarini ol
        if post_id:
            try:
                # Discussion guruhini topish
                full = await client(functions.channels.GetFullChannelRequest(entity))
                linked_chat_id = getattr(full.full_chat, "linked_chat_id", None)

                if linked_chat_id:
                    # Discussion guruhidagi shu postga reply bo'lgan xabarlar
                    discussion = await client(GetDiscussionMessageRequest(
                        peer=entity,
                        msg_id=post_id
                    ))
                    linked_entity = await client.get_entity(linked_chat_id)
                    # Discussion thread dagi barcha xabarlarni olish
                    thread_msg_id = discussion.messages[0].id if discussion.messages else None
                    if thread_msg_id:
                        msgs = await client.get_messages(
                            linked_entity,
                            reply_to=thread_msg_id,
                            limit=max_results
                        )
                        for msg in msgs:
                            if msg.text and msg.text.strip():
                                comments.append(msg.text.strip())
                else:
                    raise ValueError(
                        f"@{username} kanaliga discussion guruhi bog'lanmagan. "
                        "Kanal Settings → Discussion orqali guruh qo'shing."
                    )
            except ValueError:
                raise
            except Exception as e:
                raise ValueError(f"Post izohlarini olishda xato: {e}")

        else:
            # Post ID yo'q — kanalning oxirgi postlariga izohlarni ol
            try:
                full = await client(functions.channels.GetFullChannelRequest(entity))
                linked_chat_id = getattr(full.full_chat, "linked_chat_id", None)

                if linked_chat_id:
                    linked_entity = await client.get_entity(linked_chat_id)
                    # Discussion guruhining oxirgi xabarlarini ol
                    msgs = await client.get_messages(linked_entity, limit=max_results)
                    for msg in msgs:
                        if msg.text and msg.text.strip() and not msg.post:
                            comments.append(msg.text.strip())
                else:
                    # Discussion guruhi yo'q — guruhning o'z xabarlarini ol
                    msgs = await client.get_messages(entity, limit=max_results)
                    for msg in msgs:
                        if msg.text and msg.text.strip():
                            comments.append(msg.text.strip())
            except Exception as e:
                raise ValueError(f"Xabarlarni olishda xato: {e}")

    if not comments:
        raise ValueError(
            "Izohlar topilmadi. Sabablari:\n"
            "• Kanal/guruh izohsiz\n"
            "• Kanal discussion guruhi yo'q\n"
            "• URL to'g'ri emas\n"
            "Muqobil: izohlarni CSV/TXT sifatida eksport qilib yuklang."
        )

    result = categorize_comments(comments[:max_results])
    return {
        "platform": "Telegram",
        "title": title,
        "username": username,
        "fetched_comments": len(comments),
        **result
    }

# ── Facebook (Selenium scraping) ─────────────────────────────
def fetch_facebook_comments(url: str, access_token: str = "", max_results: int = 100) -> dict:
    """
    Facebook public post izohlarini Selenium orqali oladi.
    Login talab etmaydi — faqat public postlar.
    m.facebook.com (mobile) versiyasi ishlatiladi — ancha ochiq.
    """
    driver = get_driver()
    comments = []
    title = "Facebook Post"

    try:
        # Mobile versiya — login popup kamroq
        mobile_url = url.replace("www.facebook.com", "m.facebook.com") \
                        .replace("facebook.com", "m.facebook.com")
        if "m.facebook.com" not in mobile_url:
            mobile_url = mobile_url.replace("//facebook.com", "//m.facebook.com")
        driver.get(mobile_url)
        random_sleep(2, 4)

        # Cookie/login popup larni yopish
        for xpath in [
            "//button[contains(text(),'Accept') or contains(text(),'Allow') or contains(text(),'OK')]",
            "//a[contains(text(),'Not now') or contains(text(),'Skip')]",
            "//*[@aria-label='Close' or @aria-label='Dismiss']",
        ]:
            try:
                btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                btn.click()
                random_sleep(0.5, 1.5)
            except TimeoutException:
                pass

        # Sarlavha olish
        try:
            meta = driver.find_element(By.XPATH, "//meta[@property='og:title']")
            title = meta.get_attribute("content")[:100] or title
        except Exception:
            try:
                title = driver.title[:100] or title
            except Exception:
                pass

        scroll_attempts = 0
        max_scrolls = max(5, max_results // 8)

        while len(comments) < max_results and scroll_attempts < max_scrolls:
            # Mobile Facebook comment selectors
            comment_els = driver.find_elements(By.XPATH,
                "//*[@data-sigil='comment' or @data-sigil='comment-body']//*[self::p or self::div][not(*)]"
            )
            if not comment_els:
                comment_els = driver.find_elements(By.CSS_SELECTOR,
                    "div[data-sigil='comment'] p, "
                    "div._2b05, "
                    "div.story_body_container div[data-gt]"
                )

            for el in comment_els:
                txt = el.text.strip()
                if txt and txt not in comments and len(txt) > 2:
                    comments.append(txt)

            if len(comments) >= max_results:
                break

            # "More comments" tugmasini bosish
            clicked = False
            for xpath in [
                "//a[contains(@href,'comment_tracking')]",
                "//a[contains(text(),'more comment') or contains(text(),'View more')]",
            ]:
                try:
                    more_btn = driver.find_element(By.XPATH, xpath)
                    driver.execute_script("arguments[0].click();", more_btn)
                    random_sleep(2, 4)
                    clicked = True
                    break
                except NoSuchElementException:
                    pass

            if not clicked:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                random_sleep(2, 3)

            scroll_attempts += 1

        if not comments:
            raise ValueError(
                "Facebook izohlar topilmadi. Sabab: post private, "
                "bot-detection ishga tushgan, yoki URL noto'g'ri. "
                "Biroz kuting va qayta urinib ko'ring."
            )

    finally:
        driver.quit()

    result = categorize_comments(comments[:max_results])
    return {
        "platform": "Facebook",
        "title": title,
        "url": url,
        "fetched_comments": len(comments[:max_results]),
        **result
    }

# ── File upload parser ─────────────────────────────────────────
def parse_uploaded_file(filename: str, content: bytes) -> list:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ("docx", "doc"):
        text_content = content.decode("utf-8", errors="replace")
    else:
        text_content = ""
    if ext == "csv":
        reader = csv.DictReader(io.StringIO(text_content))
        rows = list(reader)
        if not rows:
            raise ValueError("CSV fayl bo'sh")
        fieldnames = [f.lower().strip() for f in rows[0].keys()]
        col_map = {f.lower().strip(): f for f in rows[0].keys()}
        target_col = None
        for candidate in ["text", "comment", "message", "body", "izoh", "matn"]:
            if candidate in fieldnames:
                target_col = col_map[candidate]
                break
        if not target_col:
            target_col = list(rows[0].keys())[0]
        comments = []
        for row in rows:
            cell = row.get(target_col, "").strip()
            if not cell:
                continue
            # Agar bir xonada bir necha gap bo'lsa, nuqta bo'yicha ajratamiz
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cell) if s.strip()]
            if sentences:
                comments.extend(sentences)
            else:
                comments.append(cell)
        return comments
    elif ext == "json":
        data = json.loads(text_content)
        comments = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    comments.append(item.strip())
                elif isinstance(item, dict):
                    for key in ["text", "comment", "message", "body", "izoh", "matn"]:
                        val = item.get(key, "")
                        if val:
                            comments.append(str(val).strip())
                            break
        elif isinstance(data, dict):
            for key in ["comments", "data", "items", "messages"]:
                if key in data and isinstance(data[key], list):
                    return parse_uploaded_file("temp.json", json.dumps(data[key]).encode())
        return comments
    elif ext == "txt":
        return [l.strip() for l in text_content.splitlines() if l.strip()]
    elif ext in ("docx", "doc"):
        try:
            doc = DocxDocument(io.BytesIO(content))
            lines = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                # Har bir gapni nuqta bo'yicha ajratamiz
                sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
                if sentences:
                    lines.extend(sentences)
                else:
                    lines.append(text)
            if not lines:
                raise ValueError("DOC/DOCX fayl bo'sh yoki matn topilmadi")
            return lines
        except Exception as e:
            raise ValueError(f"DOC/DOCX o'qishda xato: {e}")
    else:
        raise ValueError(f"Qo'llab-quvvatlanmaydigan fayl turi: .{ext}. Faqat CSV, JSON, TXT, DOCX.")

# ── Endpoints ──────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    tg_configured = bool(TG_API_ID and TG_API_HASH)
    yt_configured = bool(YOUTUBE_API_KEY)
    return {"status": "healthy", "telegram_configured": tg_configured, "youtube_configured": yt_configured}

@app.post("/analyze-text")
async def analyze_text(data: TextData):
    if not data.text.strip():
        raise HTTPException(400, "Matn bo'sh bo'lmasin")
    result = run_inference(data.text)
    return {"status": "success", "result": result}

@app.post("/analyze-file")
async def analyze_file(
    file: UploadFile = File(...),
    max_comments: int = Form(default=500)
):
    allowed_extensions = {"csv", "json", "txt", "docx", "doc"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(400, f"Faqat CSV, JSON, TXT, DOCX fayllari qabul qilinadi.")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "Fayl hajmi 10 MB dan oshmasligi kerak")
    try:
        comments = parse_uploaded_file(file.filename, content)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(422, f"Fayl o'qishda xato: {e}")
    except ValueError as e:
        raise HTTPException(422, str(e))
    if not comments:
        raise HTTPException(422, "Fayldan hech qanday izoh topilmadi")
    if len(comments) > max_comments:
        comments = comments[:max_comments]
    result = categorize_comments(comments)
    return {"status": "success", "result": {
        "platform": "File Upload", "title": file.filename,
        "fetched_comments": len(comments), **result
    }}

@app.post("/analyze-comments")
async def analyze_comments(req: CommentAnalysisRequest):
    url = req.url.strip()
    platform = detect_platform(url)
    try:
        if platform == "youtube":
            api_key = req.youtube_api_key or YOUTUBE_API_KEY
            if not api_key:
                raise HTTPException(400, "YouTube API key topilmadi. .env ga YOUTUBE_API_KEY qo'shing.")
            video_id = extract_youtube_id(url)
            if not video_id:
                raise HTTPException(400, "YouTube video ID topilmadi")
            result = fetch_youtube_comments(video_id, api_key, req.max_comments)
        elif platform == "instagram":
            result = fetch_instagram_comments(url, req.max_comments)
        elif platform == "telegram":
            result = await fetch_telegram_comments(url, req.max_comments)
        elif platform == "facebook":
            # Selenium scraping — access_token shart emas
            result = fetch_facebook_comments(url, req.facebook_access_token or "", req.max_comments)
        else:
            raise HTTPException(400, "Faqat YouTube, Instagram, Telegram va Facebook havolalari qabul qilinadi")
        return {"status": "success", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(422, str(e))