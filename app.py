import streamlit as st
import pandas as pd
import math

# --- 設定頁面配置 ---
st.set_page_config(page_title="深度學習影片情緒標注系統", layout="wide")

# --- 定義資料結構與常數 ---
EMOTIONS = [
    "尚未標記 (Pending)",
    "Intense Conflict (極度憤怒與厭惡)",
    "Excited Joy (以快樂和驚訝為主)",
    "Emotional Breakdown (悲傷和恐懼伴隨痛苦跡象)",
    "Calm Communication (持續的平靜狀態)",
    "Not Present (角色未出現)"
]

VIDEO_DATA = {
    "Marriage Story": {
        "url": "https://www.youtube.com/watch?v=FDFdroN7d0w",
        "duration_sec": 259, # 4:19
        "roles": ["Nicole", "Charlie"]
    },
    "2 Broke Girls": {
        "url": "https://www.youtube.com/watch?v=Wfkaq1t7C9o",
        "duration_sec": 181, # 3:01
        "roles": ["Max", "Caroline"]
    }
}

SEGMENT_LENGTH = 15  # 秒

# --- 輔助函式 ---
def generate_time_segments(duration_sec):
    """根據影片長度生成 15秒 的時間段"""
    segments = []
    total_segments = math.ceil(duration_sec / SEGMENT_LENGTH)
    
    for i in range(total_segments):
        start = i * SEGMENT_LENGTH
        end = min((i + 1) * SEGMENT_LENGTH, duration_sec)
        
        # 格式化時間字串 00:00:00
        start_str = f"{start // 3600:02}:{(start % 3600) // 60:02}:{start % 60:02}"
        end_str = f"{end // 3600:02}:{(end % 3600) // 60:02}:{end % 60:02}"
        
        segments.append({
            "Start Time": start_str,
            "End Time": end_str,
            "seconds_start": start  # 用於跳轉影片
        })
    return segments

def convert_df_to_excel(df):
    """將 DataFrame 轉為 Excel bytes"""
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# --- 主程式介面 ---

st.title("🎬 深度學習情緒標注工具")
st.markdown("### 標注說明")
st.info("""
**規則：** 每 15 秒為一個段落，請觀看左側影片，並在右側表格選擇該時段的角色情緒。
若角色在該時段未出現，請選擇 **'Not Present'**。
""")

# 1. 側邊欄：使用者設定
with st.sidebar:
    st.header("1. 設定標注目標")
    annotator_name = st.text_input("標注者姓名 (User Name)", "User")
    selected_video = st.selectbox("選擇影片", list(VIDEO_DATA.keys()))
    
    # 根據影片選擇角色
    current_roles = VIDEO_DATA[selected_video]["roles"]
    selected_role = st.selectbox("選擇標注角色", current_roles)
    
    st.markdown("---")
    st.markdown("**情緒定義速查：**")
    st.markdown("""
    - 🔴 **Intense Conflict**: 怒吼、爭執、高張力
    - 🟡 **Excited Joy**: 大笑、驚喜、正向能量
    - 🔵 **Emotional Breakdown**: 哭泣、崩潰、恐懼
    - 🟢 **Calm Communication**: 理性、平穩
    """)

# 2. 主要區域：影片與標注表
col1, col2 = st.columns([1, 1])

# 獲取當前影片資訊
video_info = VIDEO_DATA[selected_video]
segments = generate_time_segments(video_info['duration_sec'])

# 初始化 Session State (用於暫存標注資料)
session_key = f"data_{selected_video}_{selected_role}"
if session_key not in st.session_state:
    # 建立初始 DataFrame
    initial_data = []
    for seg in segments:
        initial_data.append({
            "Start Time": seg["Start Time"],
            "End Time": seg["End Time"],
            "Role": selected_role,
            "Emotion Label": "尚未標記 (Pending)",
            "Notes": ""
        })
    st.session_state[session_key] = pd.DataFrame(initial_data)

with col1:
    st.header(f"📺 影片: {selected_video}")
    # 顯示影片
    st.video(video_info['url'])
    st.caption("您可以拖動時間軸對照右側的時間段。")

with col2:
    st.header(f"📝 標注面板: {selected_role}")
    
    # 使用 Streamlit 的 Data Editor 讓使用者直接編輯表格
    # 這是最直觀的方式
    edited_df = st.data_editor(
        st.session_state[session_key],
        column_config={
            "Emotion Label": st.column_config.SelectboxColumn(
                "情緒標籤 (必選)",
                help="請選擇最符合的情緒",
                width="medium",
                options=EMOTIONS,
                required=True
            ),
            "Notes": st.column_config.TextColumn(
                "備註 (情緒線索)",
                help="例如：怒吼、哭泣",
                width="small"
            ),
            "Start Time": st.column_config.TextColumn("開始", disabled=True),
            "End Time": st.column_config.TextColumn("結束", disabled=True),
            "Role": st.column_config.TextColumn("角色", disabled=True),
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )

    # 更新 State
    st.session_state[session_key] = edited_df

    # 3. 匯出區域
    st.markdown("### 📥 輸出結果")
    
    # 檢查是否還有未標記的欄位
    pending_count = edited_df[edited_df["Emotion Label"] == "尚未標記 (Pending)"].shape[0]
    
    if pending_count > 0:
        st.warning(f"⚠️ 還有 {pending_count} 個段落尚未標記！請盡量完成後再下載。")
    else:
        st.success("✅ 所有段落已標記完成！")

    # 檔名格式
    file_name = f"{selected_role}.xlsx"
    if selected_video == "2 Broke Girls":
        # 為了區分不同影片，實際存檔時可以加上前綴，但這裡照您的需求輸出單純的角色名
        # 若需要更詳細檔名可改為 f"{selected_video}_{selected_role}.xlsx"
        pass 

    excel_data = convert_df_to_excel(edited_df)
    
    st.download_button(
        label=f"下載 Excel ({file_name})",
        data=excel_data,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )