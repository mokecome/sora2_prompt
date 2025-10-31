import streamlit as st
from templates import (
    TEMPLATES, COUNTRIES, AD_TYPES, VISUAL_STYLES,
    CAMERA_TECHNIQUES, TONES, DIRECTOR_STYLES, DURATIONS,
    CAMERA_LANGUAGE, PHYSICS_EFFECTS, AUDIO_SUGGESTIONS,
    TIMING_RHYTHM, INDUSTRY_TYPES
)
from openai import OpenAI
import os
import json
from datetime import datetime
import itertools

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

# 侧边栏 - API配置和功能模式
with st.sidebar:
    st.header("⚙️ 配置")

    # 功能模式选择
    generation_mode = st.radio(
        "生成模式",
        ["单个生成", "批量生成"],
        help="单个生成：生成一个提示词 | 批量生成：使用变量批量生成多个提示词"
    )

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="输入你的OpenAI API Key以启用AI增强功能（可选）"
    )

    st.markdown("---")

    # 批量生成配置
    if generation_mode == "批量生成":
        st.header("🔄 批量生成配置")

        # 变量数量
        num_variables = st.number_input("变量数量", min_value=1, max_value=5, value=2, help="定义多少个变量槽位")

        # 存储变量配置
        if 'variables' not in st.session_state:
            st.session_state.variables = {}

        # 动态创建变量输入
        for i in range(num_variables):
            var_key = f"变量{i+1}"
            st.subheader(f"📌 {var_key}")
            var_name = st.text_input(f"{var_key} 名称", value=f"变量{i+1}", key=f"var_name_{i}")
            var_values = st.text_area(
                f"{var_key} 值（每行一个）",
                placeholder="值1\n值2\n值3",
                height=80,
                key=f"var_values_{i}"
            )

            if var_values:
                st.session_state.variables[var_name] = [v.strip() for v in var_values.split('\n') if v.strip()]

        # 导出格式选择
        st.markdown("---")
        export_format = st.selectbox("导出格式", ["TXT", "CSV", "JSON"])
        st.session_state.export_format = export_format

    st.markdown("---")
    st.header("📚 使用说明")
    if generation_mode == "单个生成":
        st.markdown("""
        1. 选择模板或自定义参数
        2. 填写必要的元素信息
        3. 配置精确控制参数
        4. 点击生成提示词
        """)
    else:
        st.markdown("""
        1. 配置变量槽位和值
        2. 在提示词中使用 {变量名}
        3. 点击批量生成
        4. 导出所有组合结果
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

    # 视觉风格
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

    # 行业类型选择
    col_ind1, col_ind2 = st.columns(2)
    with col_ind1:
        industry_type = st.selectbox("行业类型", ["不限"] + list(INDUSTRY_TYPES.keys()))
    with col_ind2:
        if industry_type != "不限":
            industry_subtype = st.selectbox("具体类型", INDUSTRY_TYPES[industry_type])
        else:
            industry_subtype = None

    st.markdown("---")

    # 精确控制参数（折叠式展开）
    with st.expander("🎯 精确控制参数（可选）", expanded=False):
        st.caption("高级用户专用：精确控制镜头、物理效果、音频等参数")

        # 📹 镜头语言
        st.markdown("### 📹 镜头语言")
        col_cam1, col_cam2 = st.columns(2)
        with col_cam1:
            camera_type = st.multiselect("镜头类型", CAMERA_LANGUAGE["镜头类型"])
            camera_movement = st.multiselect("运镜方式", CAMERA_LANGUAGE["运镜方式"])
        with col_cam2:
            depth_of_field = st.multiselect("景深效果", CAMERA_LANGUAGE["景深效果"])
            camera_speed = st.selectbox("镜头速度", ["不限"] + CAMERA_LANGUAGE["镜头速度"])

        st.markdown("---")

        # ⚡ 物理效果
        st.markdown("### ⚡ 物理效果")
        col_phy1, col_phy2 = st.columns(2)
        with col_phy1:
            lighting = st.multiselect("光影效果", PHYSICS_EFFECTS["光影效果"])
            particles = st.multiselect("粒子效果", PHYSICS_EFFECTS["粒子效果"])
        with col_phy2:
            weather = st.selectbox("天气氛围", ["不限"] + PHYSICS_EFFECTS["天气氛围"])
            physics_sim = st.multiselect("物理模拟", PHYSICS_EFFECTS["物理模拟"])

        st.markdown("---")

        # 🎵 音频建议
        st.markdown("### 🎵 音频建议")
        col_aud1, col_aud2 = st.columns(2)
        with col_aud1:
            music_type = st.selectbox("音乐类型", ["不限"] + AUDIO_SUGGESTIONS["音乐类型"])
            sound_effects = st.multiselect("音效建议", AUDIO_SUGGESTIONS["音效建议"])
        with col_aud2:
            rhythm = st.selectbox("节奏匹配", ["不限"] + AUDIO_SUGGESTIONS["节奏匹配"])

        st.markdown("---")

        # ⏱️ 时长节奏
        st.markdown("### ⏱️ 时长节奏")
        col_tim1, col_tim2 = st.columns(2)
        with col_tim1:
            rhythm_pattern = st.selectbox("节奏分段", ["不限"] + TIMING_RHYTHM["节奏分段"])
        with col_tim2:
            shot_transition = st.selectbox("镜头切换", ["不限"] + TIMING_RHYTHM["镜头切换"])

    st.markdown("---")

    # 内容元素
    st.subheader("2. 内容元素")

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

    # 生成按钮（根据模式显示不同按钮）
    if generation_mode == "单个生成":
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            generate_btn = st.button("🎬 生成提示词", type="primary", use_container_width=True)
        with col_btn2:
            ai_enhance_btn = st.button("✨ AI增强生成", use_container_width=True, disabled=not api_key)
    else:
        generate_btn = st.button("🔄 批量生成", type="primary", use_container_width=True)
        ai_enhance_btn = False

    # 辅助函数：构建精确控制参数文本
    def build_precise_control_text():
        """构建精确控制参数的文本"""
        parts = []

        # 镜头语言
        if camera_type:
            parts.append(f"镜头类型：{', '.join(camera_type)}")
        if camera_movement:
            parts.append(f"运镜方式：{', '.join(camera_movement)}")
        if depth_of_field:
            parts.append(f"景深效果：{', '.join(depth_of_field)}")
        if camera_speed and camera_speed != "不限":
            parts.append(f"镜头速度：{camera_speed}")

        # 物理效果
        if lighting:
            parts.append(f"光影：{', '.join(lighting)}")
        if particles:
            parts.append(f"粒子效果：{', '.join(particles)}")
        if weather and weather != "不限":
            parts.append(f"天气：{weather}")
        if physics_sim:
            parts.append(f"物理模拟：{', '.join(physics_sim)}")

        # 音频建议
        if music_type and music_type != "不限":
            parts.append(f"音乐：{music_type}")
        if sound_effects:
            parts.append(f"音效：{', '.join(sound_effects)}")
        if rhythm and rhythm != "不限":
            parts.append(f"节奏：{rhythm}")

        # 时长节奏
        if rhythm_pattern and rhythm_pattern != "不限":
            parts.append(f"节奏分段：{rhythm_pattern}")
        if shot_transition and shot_transition != "不限":
            parts.append(f"镜头切换：{shot_transition}")

        return "\n".join(parts) if parts else ""

    # 生成逻辑
    def generate_prompt(use_ai=False, template_vars=None):
        """生成提示词

        Args:
            use_ai: 是否使用AI增强
            template_vars: 模板变量字典（用于批量生成）
        """
        # 如果有模板变量，使用它们替换原始值
        _brand = template_vars.get("品牌", brand_name) if template_vars else brand_name
        _theme = template_vars.get("主题", theme) if template_vars else theme
        _slogan = template_vars.get("广告语", slogan) if template_vars else slogan
        _location = template_vars.get("地点", location) if template_vars else location
        _scene = template_vars.get("场景", scene_description) if template_vars else scene_description

        # 如果选择了模板
        if selected_template != "自定义":
            base_template = TEMPLATES[selected_template]["template"]

            # 替换模板变量
            prompt = base_template.format(
                地点=_location or "{地点}",
                主题=_theme or "{主题}",
                品牌=_brand or "{品牌}",
                广告语=_slogan or "{广告语}",
                国家=country,
                场景=_scene or "{场景}",
                场景描述=_scene or "{场景描述}",
                氛围=tone,
                镜头特写=", ".join(camera_technique) if camera_technique else "{镜头特写}",
                旁白风格=tone,
                广告文案=_slogan or "{广告文案}",
                主题标语=_slogan or "{主题标语}",
                KOL="@sama",
                道具="{道具}",
                道具2="{道具2}",
                语言="英语带点亲切的中文味",
                歌词="{歌词}",
                地标="{地标}",
                主体="{主体}",
                对比场景="{对比场景}",
                细节动作="{细节动作}",
                公益主题=_theme or "{公益主题}",
                公益口号=_slogan or "{公益口号}",
                动作="{动作}",
                导演风格=director_style if director_style != "无特定风格" else "{导演风格}",
                镜头运用=", ".join(camera_technique) if camera_technique else "{镜头运用}",
                色调氛围=", ".join(visual_style) if visual_style else tone
            )
        else:
            # 自定义生成
            prompt_parts = [f"{duration}秒视频，{country}{_location}场景。"]

            # 行业类型
            if industry_type != "不限":
                prompt_parts.append(f"\n行业类型：{industry_type} - {industry_subtype if industry_subtype else ''}")

            # 视觉风格
            prompt_parts.append(f"\n视觉风格：{', '.join(visual_style) if visual_style else '自然写实'}")
            prompt_parts.append(f"镜头运用：{', '.join(camera_technique) if camera_technique else '平稳拍摄'}")
            prompt_parts.append(f"色调氛围：{tone}")

            if director_style != "无特定风格":
                prompt_parts.append(f"导演风格：{director_style}")

            # 内容元素
            prompt_parts.append(f"\n品牌：{_brand or '待定'}")
            prompt_parts.append(f"主题：{_theme or '待定'}")
            prompt_parts.append(f"广告语：{_slogan or '待定'}")

            # 场景描述
            if _scene:
                prompt_parts.append(f"\n场景描述：{_scene}")

            # 精确控制参数
            precise_control = build_precise_control_text()
            if precise_control:
                prompt_parts.append(f"\n\n【精确控制参数】\n{precise_control}")

            prompt = "\n".join(prompt_parts)

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

    # 批量生成函数
    def batch_generate():
        """批量生成提示词"""
        if not st.session_state.get('variables'):
            st.error("❌ 请先配置变量")
            return []

        # 获取所有变量的值
        var_names = list(st.session_state.variables.keys())
        var_values = list(st.session_state.variables.values())

        # 生成所有组合
        all_combinations = list(itertools.product(*var_values))

        prompts = []
        for idx, combination in enumerate(all_combinations):
            # 创建变量映射
            template_vars = dict(zip(var_names, combination))

            # 生成提示词
            prompt = generate_prompt(use_ai=False, template_vars=template_vars)
            prompts.append({
                'id': idx + 1,
                'variables': template_vars,
                'prompt': prompt
            })

        return prompts

    # 导出函数
    def export_prompts(prompts, format_type):
        """导出提示词"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type == "TXT":
            content = ""
            for p in prompts:
                content += f"=" * 80 + "\n"
                content += f"提示词 #{p['id']}\n"
                content += f"变量：{p['variables']}\n"
                content += f"-" * 80 + "\n"
                content += p['prompt'] + "\n\n"
            return content, f"sora2_prompts_{timestamp}.txt"

        elif format_type == "CSV":
            content = "ID,变量,提示词\n"
            for p in prompts:
                vars_str = str(p['variables']).replace('"', '""')
                prompt_str = p['prompt'].replace('"', '""').replace('\n', ' ')
                content += f'{p["id"]},"{vars_str}","{prompt_str}"\n'
            return content, f"sora2_prompts_{timestamp}.csv"

        elif format_type == "JSON":
            content = json.dumps(prompts, ensure_ascii=False, indent=2)
            return content, f"sora2_prompts_{timestamp}.json"

    # 显示生成结果
    if generation_mode == "单个生成":
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

    else:  # 批量生成模式
        if generate_btn:
            with st.spinner("批量生成中..."):
                prompts = batch_generate()
                if prompts:
                    st.session_state['batch_prompts'] = prompts

        if 'batch_prompts' in st.session_state:
            prompts = st.session_state['batch_prompts']
            st.success(f"✅ 已生成 {len(prompts)} 个提示词！")

            # 显示预览
            st.markdown("### 📋 生成结果预览：")
            with st.expander(f"点击查看所有 {len(prompts)} 个提示词", expanded=True):
                for p in prompts[:5]:  # 只显示前5个
                    st.markdown(f"**提示词 #{p['id']}**")
                    st.caption(f"变量: {p['variables']}")
                    st.text_area(
                        f"prompt_{p['id']}",
                        value=p['prompt'],
                        height=150,
                        label_visibility="collapsed",
                        key=f"preview_{p['id']}"
                    )
                    st.markdown("---")

                if len(prompts) > 5:
                    st.info(f"还有 {len(prompts) - 5} 个提示词未显示，请导出查看全部")

            # 导出按钮
            st.markdown("### 📥 导出选项：")
            export_format = st.session_state.get('export_format', 'TXT')
            content, filename = export_prompts(prompts, export_format)

            st.download_button(
                label=f"📥 导出为 {export_format}",
                data=content,
                file_name=filename,
                mime="text/plain" if export_format != "JSON" else "application/json",
                use_container_width=True
            )

            # 统计信息
            st.caption(f"共生成 {len(prompts)} 个提示词 | 总字数: {sum(len(p['prompt']) for p in prompts)} 字符")
        else:
            st.info("👈 请先配置变量，然后点击批量生成按钮")

# 底部
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>💡 提示：支持单个生成和批量生成 | 精确控制参数实现专业效果 | 可导出TXT/CSV/JSON格式</p>
    <p>🎬 Sora2 创意提示词生成器 v2.0 - 批量生成 + 精确控制</p>
</div>
""", unsafe_allow_html=True)
