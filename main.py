import wget
import xml.etree.ElementTree as ET
import pymorphy2
import bz2
import sqlite3

# Ma'lumotlar bazasini yaratish
conn = sqlite3.connect("words.db")

# SQL queryni bajarish
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS omonim_words (word_normal_form text, word_other_forms text)")

# Ma'lumotlar bazasini yuklab olish
def download_wikipedia_dump(dump_type):
  print("yuklab olish boshlandi.")
  url = f"https://dumps.wikimedia.org/uzwiki/latest/uzwiki-latest-{dump_type}.xml.bz2"
  wget.download(url)
  print("Barcha malumotlar yuklab olindi.")

# Ma'lumotlar bazasini o'qib olish va omonim so'zlarni ajratish
def parse_wikipedia_dump(dump_file, conn):
  print("Malumotlar bazasini shakllantirish boshlandi.")
  # Bzip2 kompressiyalangan XML faylni o'qish
  with bz2.open(dump_file, "r") as f:
      xml_data = f.read()
  # XML faylni parse qilish
  try:
    root = ET.fromstring(xml_data)
  except ET.ParseError as e:
    print(e)
    return
  # Omonim so'zlar uchun o'zgaruvchi
  morph = pymorphy2.MorphAnalyzer()

  # Sahifalarni topish
  for page in root:
    # Sahifaning nomini topish
    page_title = page.find("title").text
    print(page_title)
    # Sahifadagi matnni topish
    page_text = page.find("revision").find("text").text

    # Matnni to'plamlar bilan ajratish
    sentences = page_text.split(". ")

    # To'plamlarni tekshirish
    for sentence in sentences:
      # So'zlar bilan ajratish
      words = sentence.split(" ")

      # So'zlar bilan tekshirish
      for word in words:
        # Omonim so'zlarni topish
        parsed_word = morph.parse(word)[0]
        if parsed_word.tag.POS == "ADJF" or parsed_word.tag.POS == "NOUN":
          # Omonim bo'lgan so'zni topish
          c = conn.cursor()
          c.execute("SELECT * FROM omonim_words WHERE word_normal_form=?", (parsed_word.normal_form,))
          row = c.fetchone()

          # Omonim so'zni ma'lumotlar bazasiga qo'shish
          if row:
              # Omonim so'zni ma'lumotlar bazasiga qo'shish
              c.execute("UPDATE omonim_words SET word_other_forms=? WHERE word_normal_form=?",
                        (row[1] + ", " + parsed_word.word, parsed_word.normal_form))
          else:
              # Omonim so'zni ma'lumotlar bazasiga qo'shish
              c.execute("INSERT INTO omonim_words (word_normal_form, word_other_forms) VALUES (?, ?)",
                        (parsed_word.normal_form, parsed_word.word))
    print("Tugatildi.")
    # Ma'lumotlar bazasini saqlash
    conn.commit()
    print("Malumotlar bazasi shakllantirib bo'lindi.")


# Omonim so'zni topish
def check_word(word, conn):
    # Omonim so'zni topish
    c = conn.cursor()
    c.execute("SELECT * FROM omonim_words WHERE word_normal_form=?", (word,))
    row = c.fetchone()

    # Omonim bo'lgan so'zni topish
    if row:
        print(f"{word} so'zi omonimdir. Bu so'zning boshqa ma'nolari (formalari): {row[1]}")
    # Omonim bo'lmagan so'zni topish    print(page_title)

    else:
        print(f"{word} so'zi omonim emasdir.")


# Omonim so'zlarni avtomatik shakllantirish
def disambiguate_text(text, conn):
    c = conn.cursor()

    # Sahifadagi har bir so'zni topish
    for word in text.split():
        # Omonim so'zni topish
        c.execute("SELECT * FROM omonim_words WHERE word_normal_form=?", (word,))
        row = c.fetchone()

        # Omonim bo'lgan so'zni topish
        if row:
            print(f"{word} so'zi omonimdir. Bu so'zning boshqa ma'nolari (formalari): {row[1]}")
        # Omonim bo'lmagan so'zni topish
        else:
            print(f"{word} so'zi omonim emasdir.")

# Wikipedia aytidan malumotlarni olish jarayonini avtomatlashtirish
def wikipedia_disambiguation(text, conn):
    # Ma'lumotlar bazasini yuklab olish
    # download_wikipedia_dump("pages-articles")
    print(1)
    # Ma'lumotlar bazasini o'qib olish va omonim so'zlarni ajratish
    parse_wikipedia_dump("uzwiki-latest-pages-articles.xml.bz2", conn)
    print(2)
    # Omonim so'zlarni avtomatik shakllantirish
    # disambiguate_text(text, conn)

# Dasturni ishga tushirish
if __name__ == "__main__":
    # Matnni avtomatik shakllantirish
    wikipedia_disambiguation("Bu matnni omonim so'zlarni avtomatik shakllantirishga qo'llaniladi.", conn)

# Ma'lumotlar bazasini yopish
conn.close()
