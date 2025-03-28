import json
import os
import uuid
import random
from datetime import datetime, UTC

import openai

from DictCsv import DictCsv


# 配置 OpenAI API Key
secret_file = os.path.join(os.path.dirname(__file__), "secret.json")
with open(secret_file, "r", encoding="utf-8") as f:
    secrets = json.load(f)
OPENAI_API_KEY = secrets.get("openai_api_key")
client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.chatanywhere.tech"
)

def extract_primary_definition(definition):
    prompt = (
        "从以下释义中提取一条主要释义，严格按照'词性 + 主要解释'的格式输出，不要输出其他内容。\n"
        "示例:\n"
        "输入：n. 半径, 范围; v. 使成半径状; a. 辐射状的\n"
        "输出：n. 半径, 范围\n\n"
        f"输入：{definition}\n"
        "输出："
    )

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50
    )

    return response.choices[0].message.content.strip()

# 获取词集文件路径
test_word_set_file = os.path.join(os.path.dirname(__file__), 'data', 'word_sets', 'test.txt')

# 读取测试词集
with open(test_word_set_file, 'r') as f:
    test_word_set = f.read().splitlines()

# 读取字典 CSV
csvname = os.path.join(os.path.dirname(__file__), 'data', 'words', 'ecdict.csv')
dc = DictCsv(csvname)

# 获取当前时间戳
current_time = datetime.now(UTC).isoformat()

# 存储单词及其对应的 UUID
word_id_map = {}

# 生成单词 UUID 映射
for word in test_word_set:
    entry = dc.query(word)
    if entry:
        word_id_map[word] = str(uuid.uuid4())

# 生成 `Words` 表的 SQL 语句
words_sql_statements = []
for word, word_uuid in word_id_map.items():
    entry = dc.query(word)
    if not entry:
        continue

    word_text = entry['word'].replace("'", "''")  # 处理单引号
    pronunciation = entry['phonetic'].replace("'", "''") if entry['phonetic'] else ''
    definition = entry['translation'].replace("'", "''")
    primary_definition = extract_primary_definition(definition).replace("'", "''")
    print(primary_definition)

    sql = f"""INSERT INTO "Words" ("Id", "WordText", "Pronunciation", "Definition", "PrimaryDefinition", "ExampleSentence", "CreatedAt", "UpdatedAt") 
              VALUES ('{word_uuid}', '{word_text}', '{pronunciation}', '{definition}', '{primary_definition}', '', '{current_time}', '{current_time}');"""

    words_sql_statements.append(sql)

# 生成 `WordDistractors` 表的 SQL 语句
distractors_sql_statements = []
word_list = list(word_id_map.keys())

for word, word_uuid in word_id_map.items():
    possible_distractors = [w for w in word_list if w != word]  # 过滤掉当前单词
    distractors = random.sample(possible_distractors, min(3, len(possible_distractors)))  # 选取 3 个干扰项

    for distractor in distractors:
        distractor_uuid = word_id_map[distractor]
        sql = f"""INSERT INTO "WordDistractors" ("Id", "WordId", "DistractorId", "CreatedAt", "UpdatedAt") 
                  VALUES ('{uuid.uuid4()}', '{word_uuid}', '{distractor_uuid}', '{current_time}', '{current_time}');"""
        distractors_sql_statements.append(sql)

# 生成 `WordBooks` 表的 SQL 语句（创建 "Test" 单词书）
word_book_id = str(uuid.uuid4())  # 生成 "Test" 单词书的 UUID
word_books_sql = f"""INSERT INTO "WordBooks" ("Id", "WordBookName", "CreatedAt", "UpdatedAt") 
                     VALUES ('{word_book_id}', 'Test', '{current_time}', '{current_time}');"""

# 生成 `WordWordBooks` 关系表的 SQL 语句（所有单词加入 "Test" 单词书）
word_word_books_sql_statements = [
    f"""INSERT INTO "WordWordBooks" ("Id", "WordId", "BookId", "CreatedAt", "UpdatedAt") 
        VALUES ('{uuid.uuid4()}', '{word_uuid}', '{word_book_id}', '{current_time}', '{current_time}');"""
    for word_uuid in word_id_map.values()
]

# 输出 SQL 语句到文件
with open("insert_data.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(words_sql_statements) + "\n")
    f.write("\n".join(distractors_sql_statements) + "\n")
    f.write(word_books_sql + "\n")
    f.write("\n".join(word_word_books_sql_statements))

print("SQL 语句已生成并保存至 insert_data.sql")
