"""
Scrape komentar TikTok (username dan komentar) - SEMUA LEVEL
Versi 4.0 — Fixed: Ambil semua level komentar + expand replies
"""

import os
import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    SessionNotCreatedException,
    ElementClickInterceptedException,
)

# ===================== KONFIGURASI =====================
MAX_SCROLL_BATCH = 300
STAGNANT_LIMIT = 8
SCROLL_DELAY = 1.5
WAIT_SEC = 25

CSV_PATH = "tiktok_comments.csv"
JSON_PATH = "tiktok_comments.json"

# GANTI sesuai profil Edge kamu
EDGE_USER_DATA_DIR = r"C:\Users\Dell\AppData\Local\Microsoft\Edge\User Data"
PROFILE_DIR = "Default"
# =======================================================


def build_driver():
    """Bangun driver Edge dengan profil login"""
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument(f"--user-data-dir={EDGE_USER_DATA_DIR}")
    opts.add_argument(f"--profile-directory={PROFILE_DIR}")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-component-update")
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    return webdriver.Edge(options=opts)


def click_if_present(driver, by, sel, timeout=3):
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, sel)))
        el.click()
        return True
    except Exception:
        return False


def wait_for_comment_container(driver):
    """Pastikan daftar komentar muncul"""
    selectors = [
        "[data-e2e='browse-comment-list']",
        "[data-e2e='comment-list']",
        "section[aria-label*='omment']",
        "div[class*='CommentList']",
    ]
    for sel in selectors:
        try:
            el = WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            if el.is_displayed():
                return el
        except Exception:
            continue

    click_if_present(driver, By.CSS_SELECTOR, "[data-e2e='comment-icon'], [data-e2e='browse-comment-icon']", 5)
    try:
        el = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-e2e='browse-comment-list']")))
        return el
    except TimeoutException:
        with open("debug_video_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise TimeoutException("Komentar tidak muncul. Lihat debug_video_page.html.")


def find_scrollable_ancestor(driver, element):
    """Cari elemen scrollable di DOM"""
    return driver.execute_script("""
        function findScrollable(el){
            let e = el;
            while(e){
                const cs = getComputedStyle(e);
                const sc = (e.scrollHeight > e.clientHeight) && /(auto|scroll)/.test(cs.overflowY);
                if (sc) return e;
                e = e.parentElement;
            }
            return document.scrollingElement;
        }
        return findScrollable(arguments[0]);
    """, element)


def expand_all_replies(driver):
    """
    Klik semua tombol 'View more replies' / 'Lihat balasan'
    untuk membuka balasan tersembunyi
    """
    max_attempts = 3
    clicked_total = 0
    
    for attempt in range(max_attempts):
        try:
            # XPath untuk berbagai variasi teks
            reply_buttons = driver.find_elements(
                By.XPATH, 
                "//p[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'replies')] | "
                "//p[contains(text(), 'Lihat balasan')] | "
                "//p[contains(text(), 'more replies')] | "
                "//button[contains(., 'View more replies')] | "
                "//button[contains(., 'Lihat balasan')]"
            )
            
            if not reply_buttons:
                break
            
            clicked_in_round = 0
            for btn in reply_buttons:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                        time.sleep(0.2)
                        try:
                            btn.click()
                            clicked_in_round += 1
                            time.sleep(0.4)
                        except ElementClickInterceptedException:
                            driver.execute_script("arguments[0].click();", btn)
                            clicked_in_round += 1
                            time.sleep(0.4)
                except:
                    continue
            
            clicked_total += clicked_in_round
            if clicked_in_round == 0:
                break
                
        except Exception as e:
            break
    
    if clicked_total > 0:
        print(f"  ↳ Expanded {clicked_total} reply threads")
    return clicked_total


def click_view_more_comments(driver):
    """Klik 'View more comments' untuk load komentar tambahan"""
    try:
        btns = driver.find_elements(By.CSS_SELECTOR, "[data-e2e='browse-comment-view-more']")
        for b in btns:
            if b.is_displayed() and b.is_enabled():
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
                time.sleep(0.3)
                try:
                    b.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", b)
                return True
    except Exception:
        pass

    # fallback via teks
    try:
        b = driver.find_element(
            By.XPATH,
            "//button[contains(.,'View more') or contains(.,'Lihat lainnya') or contains(.,'Lihat lebih banyak')]",
        )
        if b.is_displayed():
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
            time.sleep(0.2)
            b.click()
            return True
    except Exception:
        pass
    return False


def grab_comments_batch(driver, seen, out_list):
    """
    Ambil SEMUA level komentar (level 1, 2, 3, dst)
    dengan multiple selector fallback
    """
    # Coba berbagai selector untuk wrapper komentar
    wrapper_selectors = [
        "div[class*='DivCommentObjectWrapper']",
        "div[class*='DivCommentItemContainer']",
        "div[data-e2e='comment-item']",
        "div[class*='CommentItem']"
    ]
    
    items = []
    for selector in wrapper_selectors:
        found = driver.find_elements(By.CSS_SELECTOR, selector)
        if found:
            items = found
            break
    
    if not items:
        # Fallback terakhir: cari semua div yang punya username + comment
        items = driver.find_elements(By.XPATH, "//div[.//span[@data-e2e='comment-level-1'] or .//span[@data-e2e='comment-level-2'] or .//span[@data-e2e='comment-level-3']]")
    
    for item in items:
        try:
            # === AMBIL USERNAME ===
            username = ""
            username_selectors = [
                "[data-e2e='comment-username-1'] p",
                "[data-e2e='comment-username-2'] p",
                "[data-e2e='comment-username-3'] p",
                "a[data-e2e*='comment-username'] p",
                "span[class*='SpanUserNameText']",
                "a[class*='StyledUserLinkName'] span"
            ]
            
            for sel in username_selectors:
                try:
                    username_el = item.find_element(By.CSS_SELECTOR, sel)
                    username = username_el.text.strip()
                    if username:
                        break
                except:
                    continue
            
            # Fallback: cari via XPath
            if not username:
                try:
                    username_el = item.find_element(By.XPATH, ".//a[contains(@data-e2e, 'comment-username')]//span")
                    username = username_el.text.strip()
                except:
                    pass
            
            # === AMBIL KOMENTAR (SEMUA LEVEL) ===
            comment_text = ""
            comment_selectors = [
                "span[data-e2e='comment-level-1']",
                "span[data-e2e='comment-level-2']",
                "span[data-e2e='comment-level-3']",
                "span[data-e2e='comment-level-4']",
                "span[class*='SpanText']",
                "p[data-e2e='comment-text-1']",
                "div[class*='DivCommentText'] span"
            ]
            
            for sel in comment_selectors:
                try:
                    comment_el = item.find_element(By.CSS_SELECTOR, sel)
                    comment_text = comment_el.text.strip()
                    if comment_text:
                        break
                except:
                    continue
            
            # Fallback: ambil semua text dalam comment container
            if not comment_text:
                try:
                    comment_el = item.find_element(By.XPATH, ".//span[contains(@data-e2e, 'comment-level')]")
                    comment_text = comment_el.text.strip()
                except:
                    pass
            
            # Simpan jika valid
            key = (username, comment_text)
            if key not in seen and username and comment_text:
                seen.add(key)
                out_list.append({
                    "username": username,
                    "comment": comment_text
                })
        except Exception as e:
            continue


def main():
    os.system("taskkill /F /IM msedge.exe >NUL 2>&1")

    # === Input URL dari user ===
    print("=" * 60)
    print("TikTok Comment Scraper v4.0 - All Levels")
    print("=" * 60)
    video_url = input("\nMasukkan URL video TikTok: ").strip()
    if not video_url.startswith("http"):
        print("❌ URL tidak valid. Pastikan dimulai dengan https://")
        return

    print("\n🔄 Membuka browser...")
    try:
        driver = build_driver()
    except SessionNotCreatedException:
        opts = Options()
        opts.add_argument("--start-maximized")
        opts.add_argument(f"--user-data-dir={EDGE_USER_DATA_DIR}")
        opts.add_argument(f"--profile-directory={PROFILE_DIR}")
        opts.add_argument("--disable-gpu")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Edge(options=opts)

    wait = WebDriverWait(driver, WAIT_SEC)

    try:
        print("🌐 Loading video...")
        driver.get(video_url)
        wait.until(EC.url_contains("/video/"))

        # Buka panel komentar jika tertutup
        click_if_present(driver, By.CSS_SELECTOR, "[data-e2e='comment-icon'], [data-e2e='browse-comment-icon']", 5)

        print("⏳ Menunggu komentar load...")
        container = wait_for_comment_container(driver)
        scrollable = find_scrollable_ancestor(driver, container)

        seen, comments = set(), []
        last_len, stagnant = -1, 0

        print("\n🔍 Mulai scraping komentar...\n")
        
        for batch in range(MAX_SCROLL_BATCH):
            # 1. Expand semua replies terlebih dahulu
            expand_all_replies(driver)
            
            # 2. Ambil semua komentar (level 1, 2, 3, dst)
            grab_comments_batch(driver, seen, comments)
            
            # 3. Klik "View more comments"
            clicked = click_view_more_comments(driver)
            if clicked:
                time.sleep(0.8)

            # 4. Cek stagnasi
            if len(comments) == last_len:
                stagnant += 1
            else:
                stagnant, last_len = 0, len(comments)
            
            # Print progress setiap 10 batch
            if (batch + 1) % 10 == 0:
                print(f"📊 Batch {batch + 1}/{MAX_SCROLL_BATCH} | Total: {len(comments)} komentar")
            
            if stagnant >= STAGNANT_LIMIT:
                print(f"\n⚠️  Tidak ada komentar baru setelah {STAGNANT_LIMIT} scroll, menghentikan...")
                break

            # 5. Scroll ke bawah
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollTop + Math.max(300, arguments[0].clientHeight*0.9);",
                scrollable
            )
            time.sleep(SCROLL_DELAY)

        # Simpan hasil
        print("\n💾 Menyimpan hasil...")
        pd.DataFrame(comments).to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print(f"✅ SELESAI! Total komentar: {len(comments)}")
        print("=" * 60)
        print(f"📄 CSV  : {CSV_PATH}")
        print(f"📄 JSON : {JSON_PATH}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Simpan debug HTML
        with open("debug_video_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        time.sleep(1)
        driver.quit()
        print("\n🔒 Browser ditutup.")


if __name__ == "__main__":
    main()