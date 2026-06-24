import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

# =====================================================================
# 1. ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ
# =====================================================================
def get_db_connection():
    try:
        # Рекомендуется, чтобы в secrets строка заканчивалась на ?sslmode=require
        return psycopg2.connect(st.secrets["postgres"]["url"])
    except Exception as e:
        st.error(f"Не удалось подключиться к базе данных. Проверьте Secrets или статус БД. Ошибка: {e}")
        return None

# Инициализируем таблицы в БД (если их еще нет)
def init_db():
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    lessons_count INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        conn.close()

# Запускаем проверку базы данных при старте
init_db()

# =====================================================================
# 2. ПОЛНЫЙ СИММЕТРИЧНЫЙ СЛОВАРЬ ЛОКАЛИЗАЦИИ (Исправлен SyntaxError и KeyError)
# =====================================================================
LANGUAGES = {
    "RU": {
        "page_title": "Трекер обучения",
        "title": "🎓 Персональный трекер обучения",
        "metric_courses": "Всего курсов в БД",
        "metric_hours": "Общее время (часов)",
        "sb_header": "➕ Добавить новый курс",
        "sb_course_name": "Название курса:",
        "sb_placeholder": "например, CS50 Python",
        "sb_lessons_count": "Количество уроков в курсе:",
        "sb_submit": "Создать трек",
        "sb_success": "Курс '{}' успешно добавлен!",
        "lesson_status_progress": "⏳ В процессе",
        "min_label": "мин.",
        "hist_total_time": "⏱️ `Общее время урока:` **{} мин.** | `🧠 Настроение:` {}",
        "hist_last_update": "📅 `Последнее обновление:` {}",
        "hist_notes": "💬 `Заметки / Комментарии:`",
        "btn_del_lesson": "🗑️ Удалить урок",
        "sidebar_theme": "🎨 Настройки интерфейса",
        "bg_color_label": "Цвет фона",
        "text_color_label": "Цвет текста"
    },
    "EN": {
        "page_title": "My Study Tracker",
        "title": "🎓 Personal Study Tracker",
        "metric_courses": "Total courses in DB",
        "metric_hours": "Total study time (hours)",
        "sb_header": "➕ Add New Course",
        "sb_course_name": "Course name:",
        "sb_placeholder": "e.g., CS50 Python",
        "sb_lessons_count": "Number of lessons in course:",
        "sb_submit": "Create tracking",
        "sb_success": "Course '{}' successfully added!",
        "lesson_status_progress": "⏳ In progress",
        "min_label": "min.",
        "hist_total_time": "⏱️ `Total lesson time:` **{} min.** | `🧠 Mood:` {}",
        "hist_last_update": "📅 `Last update:` {}",
        "hist_notes": "💬 `Notes / Comments:`",
        "btn_del_lesson": "🗑️ Delete lesson",
        "sidebar_theme": "🎨 UI Settings",
        "bg_color_label": "Background color",
        "text_color_label": "Text color"
    }
}

# =====================================================================
# 3. ИНИЦИАЛИЗАЦИЯ И ВЫБОР ЯЗЫКА
# =====================================================================
if "lang" not in st.session_state:
    st.session_state.lang = "RU"

# Переключатель языка на самом верху сайдбара
st.session_state.lang = st.sidebar.selectbox(
    "🌐 Language / Язык",
    options=["RU", "EN"],
    index=0 if st.session_state.lang == "RU" else 1
)
lang = st.session_state.lang

# Конфигурация страницы должна вызываться до основных виджетов
st.set_page_config(page_title=LANGUAGES[lang]["page_title"], layout="wide")

# =====================================================================
# 4. НАСТРОЙКИ ИНТЕРФЕЙСА (Сохранение цвета без сброса)
# =====================================================================
st.sidebar.markdown(f"### {LANGUAGES[lang]['sidebar_theme']}")

# Читаем сохраненные цвета из URL параметров браузера, либо берем дефолт
initial_bg = st.query_params.get("bg_color", "#ffffff")
initial_text = st.query_params.get("text_color", "#31333F")

# Используем постоянный `key`. Теперь при смене языка виджет не пересоздается с нуля
bg_color = st.sidebar.color_picker(
    LANGUAGES[lang]["bg_color_label"], 
    value=initial_bg, 
    key="persistent_bg_picker"
)
text_color = st.sidebar.color_picker(
    LANGUAGES[lang]["text_color_label"], 
    value=initial_text, 
    key="persistent_text_picker"
)

# Записываем выбранные цвета обратно в URL-параметры (сохраняются при обновлении страницы)
st.query_params["bg_color"] = bg_color
st.query_params["text_color"] = text_color

# Инжектим CSS для динамической смены темы
custom_css = f"""
<style>
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: {text_color} !important;
    }}
</style>
    """
st.markdown(custom_css, unsafe_allow_html=True)

# =====================================================================
# 5. ГЛАВНЫЙ ЭКРАН И МЕТРИКИ
# =====================================================================
st.title(LANGUAGES[lang]["title"])

courses_count = 0
total_hours = 0.0

# Получаем актуальные данные для метрик из БД
conn = get_db_connection()
if conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM courses;")
        courses_count = cur.fetchone()[0]
    conn.close()

col1, col2 = st.columns(2)
col1.metric(LANGUAGES[lang]["metric_courses"], courses_count)
col2.metric(LANGUAGES[lang]["metric_hours"], f"{total_hours:.1f}")

st.markdown("---")

# =====================================================================
# 6. ФОРМА ДОБАВЛЕНИЯ КУРСА (Убирает надоедливый "Press Enter")
# =====================================================================
# Обернув элементы в st.sidebar.form, мы убираем подсказки "Press Enter" у text_input
with st.sidebar.form(key="add_course_form", clear_on_submit=True):
    st.markdown(f"### {LANGUAGES[lang]['sb_header']}")
    
    course_name = st.text_input(
        LANGUAGES[lang]["sb_course_name"], 
        placeholder=LANGUAGES[lang]["sb_placeholder"]
    )
    
    lessons_count = st.number_input(
        LANGUAGES[lang]["sb_lessons_count"], 
        min_value=1, 
        max_value=1000, 
        value=10
    )
    
    # Кнопка отправки формы
    submit_clicked = st.form_submit_button(LANGUAGES[lang]["sb_submit"])

# Обработка отправки формы вынесена за ее пределы
if submit_clicked:
    if not course_name.strip():
        st.sidebar.error("Название курса не может быть пустым!" if lang == "RU" else "Course name cannot be empty!")
    else:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO courses (name, lessons_count) VALUES (%s, %s);",
                    (course_name.strip(), lessons_count)
                )
                conn.commit()
            conn.close()
            st.sidebar.success(LANGUAGES[lang]["sb_success"].format(course_name))
            st.rerun()  # Перезапускаем приложение для мгновенного обновления метрик

# =====================================================================
# 7. ВЫВОД СПИСКА КУРСОВ ИЗ БАЗЫ ДАННЫХ
# =====================================================================
st.subheader("Мои курсы" if lang == "RU" else "My Courses")

conn = get_db_connection()
if conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM courses ORDER BY created_at DESC;")
        courses = cur.fetchall()
    conn.close()
    
    if not courses:
        st.info("У вас пока нет добавленных курсов." if lang == "RU" else "No courses added yet.")
    else:
        for course in courses:
            # Рендерим каждый курс в аккуратный выпадающий список (Expander)
            with st.expander(f"📚 {course['name']} ({course['lessons_count']} уроков / lessons)"):
                st.write(LANGUAGES[lang]["lesson_status_progress"])
                
                # Демонстрация использования оставшихся ключей твоего словаря:
                st.write(LANGUAGES[lang]["hist_notes"])
                st.text_area("Комментарий к курсу", placeholder="...", key=f"notes_{course['id']}", label_visibility="collapsed")
                
                # Кнопка удаления курса
                if st.button(LANGUAGES[lang]["btn_del_lesson"], key=f"del_{course['id']}"):
                    conn = get_db_connection()
                    if conn:
                        with conn.cursor() as cur:
                            cur.execute("DELETE FROM courses WHERE id = %s;", (course['id'],))
                            conn.commit()
                        conn.close()
                        st.rerun()
