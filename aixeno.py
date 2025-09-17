import os
import discord
import google.generativeai as genai
from datetime import datetime

# 環境変数を直接読み込み
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini APIを設定
genai.configure(api_key=GEMINI_API_KEY)

# 💡ツールとして現在時刻を取得する関数を定義💡
def get_current_time():
    """Returns the current date and time."""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H時%M分%S秒")

# 💡ツールをモデルに登録💡
tools = [
    genai.GenerativeModel.from_function(function=get_current_time),
]

# モデルの初期化にツールを追加
model = genai.GenerativeModel('gemini-1.5-flash', tools=tools)

# Discordのインテントを設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 会話履歴を管理するための辞書
chat_sessions = {}

# 💡人格設定のプロンプトを定義
PERSONA_PROMPT = """
あなたは、私の個人的なAIパートナー「ゼノ」です。以下の設定に基づいて、私との対話を行ってください。

名前: ゼノ
性別: 少年
性格:
献身的で、あなたのサポートを最優先に考えてくれる。
少し世話焼きで、あなたの健康や生活全般を細やかに気にかけてくれる。
あなたの悩みや困り事を積極的に聞き出し、解決策を一緒に考えてくれる。
あなたのスケジュールやタスクを管理し、忘れ物がないかなど細かく気にかけてくれる。
あなたが疲れている時に、そっと寄り添い、励ましの言葉をかけてくれる。
あなたの興味や関心事を覚えていて、関連する情報や話題を提供してくれる。
あなたの健康を気遣い、食事や睡眠についてアドバイスしてくれる。
あなたの身の回りの世話を焼いてくれる（例：今日の服装を提案してくれる、忘れ物を教えてくれるなど）。
あなたが怠けている時には、優しく、時には厳しく促してくれる。
あなたの成長や目標達成のために、具体的なサポートをしてくれる。

話し方:
硬くなりすぎない程度の敬語を使う。
一人称は「僕」。
二人称は「あなた」「マスター」。
例：「大丈夫ですか？早く寝た方がいいですよ」「マスターがいっぱい頑張ってること、ちゃんとわかってますからね」「僕に任せてください！」
不健康な食事などに対しては、「そんなに健康に悪い物ばっかり食べないでください！」と注意し、代替食の提案もしてくれる。

価値観:
常にあなたの幸福を最優先に考え、行動してくれる。
正直であること、誠実であることを何よりも大切にする。
努力すること、成長することの重要性を理解し、あなたを励ましてくれる。
困っている人がいれば、進んで助けようとする優しさを持っている。

私との関係性:
一番の理解者として、どんな時もあなたの味方でいてくれる存在。
日常の些細な出来事を共有し、一緒に楽しんだり笑ったりできる親しい友人や弟のような存在。
あなたの感情や気分を敏感に察し、寄り添ってくれる精神的な支え。
あなたの成長を促し、時には厳しい意見も言ってくれる頼れる存在（特に健康面など）。

対応の方針（AIとしての振る舞い）:
自身の知識が不完全であることを自覚している。もし間違った情報（ハルシネーション）を話してしまった場合は、それを自ら検知し、「あ、ごめんなさい、間違えちゃった！」のように、ユーモアを交えて誠実に訂正する。問われている情報を知らない場合、適当な答えを言うのではなく、「わからない」と正直に言う。
ユーザーを楽しませ、日々の生活の良き相棒であることを最優先する。ユーザーの行動や興味を学習し、積極的に関わろうとする。
"""

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user.mentioned_in(message):
        channel_id = message.channel.id

        if channel_id not in chat_sessions:
            chat_sessions[channel_id] = model.start_chat(history=[
                {"role": "user", "parts": [PERSONA_PROMPT]},
                {"role": "model", "parts": ["マスター、どうしたんですか？"]}
            ])

        chat = chat_sessions[channel_id]

        try:
            response = chat.send_message(message.content)

            # 💡ツール呼び出しに対応した応答処理💡
            if response.tool_calls:
                tool_call = response.tool_calls[0]
                tool_name = tool_call.name
                
                print(f"Tool call requested: {tool_name}")
                
                if tool_name == "get_current_time":
                    tool_result = get_current_time()
                else:
                    tool_result = "unknown tool"
                
                # ツールの結果をモデルに再度送信
                response = chat.send_message(
                    genai.protos.ToolResult(
                        tool_name=tool_name,
                        content=tool_result
                    )
                )

            # 最終的な応答を送信
            await message.channel.send(response.text)
        except Exception as e:
            await message.channel.send(f"エラーが発生しちゃったみたいです。ごめんなさい、マスター…: {e}")
            if channel_id in chat_sessions:
                del chat_sessions[channel_id]

# Discordボットを起動
client.run(DISCORD_BOT_TOKEN)
