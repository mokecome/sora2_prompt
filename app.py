import streamlit as st
from templates import (
    TEMPLATES, COUNTRIES, AD_TYPES, VISUAL_STYLES,
    CAMERA_TECHNIQUES, TONES, DIRECTOR_STYLES, DURATIONS
)
from openai import OpenAI
import os

# Helper function to initialize OpenAI client safely
def create_openai_client(api_key):
    """
    Create OpenAI client with proper configuration.
    Handles proxy settings properly for OpenAI v1.0+
    """
    # Remove any proxy-related environment variables that might interfere
    # OpenAI v1.0+ uses httpx which respects HTTP_PROXY/HTTPS_PROXY env vars
    # but doesn't accept 'proxies' as a constructor parameter
    try:
        client = OpenAI(
            api_key=api_key,
            max_retries=2,
            timeout=30.0
        )
        return client
    except TypeError as e:
        if "proxies" in str(e):
            # If proxies parameter is being passed incorrectly, try with minimal config
            client = OpenAI(api_key=api_key)
            return client
        else:
            raise

# 页面配置
st.set_page_config(
    page_title="Sora2 创意提示词生成器",
    page_icon="🎬",
    layout="wide"
)

# 标题
st.title("🎬 Sora2 创意提示词生成器")
st.markdown("---")

# 侧边栏 - API配置
with st.sidebar:
    st.header("⚙️ 配置")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="输入你的OpenAI API Key以启用AI增强功能（可选）"
    )

    st.markdown("---")
    st.header("📚 使用说明")
    st.markdown("""
    1. 选择模板或自定义参数
    2. 填写必要的元素信息
    3. 点击生成提示词
    4. 复制结果用于Sora2
    """)

# 主界面 - 左右两栏
col1, col2 = st.columns([1, 1])

with col1:
    st.header("🎨 提示词元素控制")

    # 模板与基础设置
    st.subheader("1. 模板与基础设置")

    # 模板选择
    template_options = ["自定义"] + list(TEMPLATES.keys())
    selected_template = st.selectbox(
        "预设模板",
        template_options,
        help="选择一个预设模板或自定义创建"
    )

    if selected_template != "自定义":
        st.info(f"📝 {TEMPLATES[selected_template]['name']}")

    # 基础设置
    col_a, col_b = st.columns(2)
    with col_a:
        country = st.selectbox("国家/地区", COUNTRIES)
        location = st.text_input("具体地点", placeholder="例如：长沙")

    with col_b:
        duration = st.select_slider("时长（秒）", options=DURATIONS, value=10)
        ad_category = st.selectbox("广告类型", list(AD_TYPES.keys()))

    st.markdown("---")

    # 视觉风格
    st.subheader("2. 视觉风格")

    visual_style = st.multiselect(
        "视觉风格（可多选）",
        VISUAL_STYLES,
        default=["黑白高对比"] if selected_template == "Nike运动广告" else []
    )

    camera_technique = st.multiselect(
        "镜头运用（可多选）",
        CAMERA_TECHNIQUES,
        default=["快速切换"] if selected_template == "Nike运动广告" else []
    )

    tone = st.selectbox("色调/氛围", TONES)

    director_style = st.selectbox("导演风格", DIRECTOR_STYLES)

    st.markdown("---")

    # 内容元素
    st.subheader("3. 内容元素")

    brand_name = st.text_input("品牌名称", placeholder="例如：长沙臭豆腐")
    theme = st.text_input("主题/产品", placeholder="例如：臭豆腐")
    slogan = st.text_area("广告语/文案", placeholder="例如：Anytime，臭豆腐 Time！")

    # 自定义场景描述
    scene_description = st.text_area(
        "场景描述（可选）",
        placeholder="详细描述场景、道具、人物等...",
        height=100
    )

with col2:
    st.header("📄 生成结果")

    # 生成按钮
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        generate_btn = st.button("🎬 生成提示词", type="primary", use_container_width=True)
    with col_btn2:
        ai_enhance_btn = st.button("✨ AI增强生成", use_container_width=True, disabled=not api_key)

    # 生成逻辑
    def generate_prompt(use_ai=False):
        """生成提示词"""

        # 如果选择了模板
        if selected_template != "自定义":
            base_template = TEMPLATES[selected_template]["template"]

            # 替换模板变量
            prompt = base_template.format(
                地点=location or "{地点}",
                主题=theme or "{主题}",
                品牌=brand_name or "{品牌}",
                广告语=slogan or "{广告语}",
                国家=country,
                场景=scene_description or "{场景}",
                场景描述=scene_description or "{场景描述}",
                氛围=tone,
                镜头特写=", ".join(camera_technique) if camera_technique else "{镜头特写}",
                旁白风格=tone,
                广告文案=slogan or "{广告文案}",
                主题标语=slogan or "{主题标语}",
                KOL="@sama",
                道具="{道具}",
                道具2="{道具2}",
                语言="英语带点亲切的中文味",
                歌词="{歌词}",
                地标="{地标}",
                主体="{主体}",
                对比场景="{对比场景}",
                细节动作="{细节动作}",
                公益主题=theme or "{公益主题}",
                公益口号=slogan or "{公益口号}",
                动作="{动作}",
                导演风格=director_style if director_style != "无特定风格" else "{导演风格}",
                镜头运用=", ".join(camera_technique) if camera_technique else "{镜头运用}",
                色调氛围=", ".join(visual_style) if visual_style else tone
            )
        else:
            # 自定义生成
            prompt = f"""{duration}秒广告，{country}{location}场景。

视觉风格：{", ".join(visual_style) if visual_style else "自然写实"}
镜头运用：{", ".join(camera_technique) if camera_technique else "平稳拍摄"}
色调氛围：{tone}
{f"导演风格：{director_style}" if director_style != "无特定风格" else ""}

品牌：{brand_name or "待定"}
主题：{theme or "待定"}
广告语：{slogan or "待定"}

{f"场景描述：{scene_description}" if scene_description else ""}
"""

        # AI增强
        if use_ai and api_key:
            try:
                # Use helper function to create OpenAI client safely
                client = create_openai_client(api_key)
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "你是一个专业的Sora2视频提示词专家。请优化和丰富用户提供的提示词，使其更加生动、具体、适合AI视频生成。保持原有风格和核心内容，增加细节描述。"},
                        {"role": "user", "content": f"请优化以下Sora2提示词：\n\n{prompt}"}
                    ],
                    temperature=0.7
                )
                prompt = response.choices[0].message.content
                st.success("✅ AI增强完成！")
            except TypeError as e:
                if "proxies" in str(e):
                    st.error("❌ AI增强失败: 代理配置错误。OpenAI v1.0+ 不支持 'proxies' 参数。请使用 HTTP_PROXY/HTTPS_PROXY 环境变量配置代理。")
                else:
                    st.error(f"❌ AI增强失败: {str(e)}")
            except Exception as e:
                st.error(f"❌ AI增强失败: {str(e)}")

        return prompt

    # 显示生成结果
    if generate_btn:
        result = generate_prompt(use_ai=False)
        st.session_state['generated_prompt'] = result

    if ai_enhance_btn:
        if not api_key:
            st.error("请先在侧边栏输入OpenAI API Key")
        else:
            with st.spinner("AI增强生成中..."):
                result = generate_prompt(use_ai=True)
                st.session_state['generated_prompt'] = result

    # 显示结果
    if 'generated_prompt' in st.session_state:
        st.markdown("### 生成的提示词：")

        # 文本框显示
        result_text = st.text_area(
            "提示词内容",
            value=st.session_state['generated_prompt'],
            height=400,
            label_visibility="collapsed"
        )

        # 复制按钮
        st.code(st.session_state['generated_prompt'], language="text")
        st.success("✅ 提示词已生成！请复制上方文本使用。")

        # 统计信息
        st.caption(f"字数统计: {len(st.session_state['generated_prompt'])} 字符")
    else:
        st.info("👈 请在左侧配置参数后点击生成按钮")

# 底部
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>💡 提示：选择预设模板可快速生成专业提示词 | 自定义模式支持完全个性化创作</p>
    <p>🎬 Sora2 创意提示词生成器 v1.0</p>
</div>
""", unsafe_allow_html=True)
