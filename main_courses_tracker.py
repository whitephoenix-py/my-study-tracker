import streamlit as st
import psycopg2
import time
import re
from datetime import datetime

# ==========================================================
# 1. СЛОВАРЬ ЛОКАЛИЗАЦИИ (RU / EN)
# ==========================================================
LANGUAGES = {
    "RU": {
        "page_title": "Мой Трекер Обучения",
        "title": "🎓 Персональный трекер обучения",
        "metric_courses": "Всего курсов в базе",
        "metric_hours": "Общее время в учебе (часы)",
        "sb_header": "➕ Добавить новый курс",
        "sb_course_name": "Название курса:",
        "sb_placeholder": "например, CS50 Python",
        "sb_lessons_count": "Количество уроков в курсе:",
        "sb_submit": "Создать отслеживание",
        "sb_success": "Курс '{}' успешно добавлен!",
        "tab_active": "🚀 Активные курсы",
        "tab_completed": "📦 Пройденные (Архив)",
        "folder_empty": "В этой папке пока ничего нет.",
        "course_stats": "⏱️ Налетано: **{} ч.** | Пройдено уникальных уроков: **{} из {}**",
        "progress_label": "Прогресс: **{}%**",
        "manage_course": "🗑️ Управление курсом",
        "delete_warn": "Удалить '{}'?",
        "delete_confirm": "Да, удалить окончательно",
        "exp_active_title": "⏳ ИДЕТ ЗАНЯТИЕ! (Нажмите для остановки)",
        "exp_inactive_title": "⚡ Занятие и История уроков",
        "archive_msg": "🎉 Этот курс полностью пройден! Доступен только просмотр истории.",
        "btn_start": "⏱️ Начать занятие",
        "timer_running": "Таймер запущен. Прошло минут: {}",
        "lesson_title_lbl": "Название урока:",
        "lesson_placeholder": "например, Урок 1",
        "comment_lbl": "Что прошли? (комментарий):",
        "mood_lbl": "Ваше настроение:",
        "mood_options": ["🔥 Заряжен / Все понял", "🟢 Хорошо / Двигаюсь дальше", "🟡 Нормально / Сложновато", "🔴 Устал / Ничего не понял"],
        "is_done_lbl": "✅ Этот урок полностью завершен?",
        "btn_stop": "🛑 Завершить сессию",
        "err_format": "🛑 ОШИБКА: Пожалуйста, используйте формат 'Урок X' (например: Урок 1, Урок 2).",
        "err_max_lessons": "🛑 ОШИБКА: В этом курсе запланировано всего {} уроков!",
        "err_already_done": "🛑 ОШИБКА: '{}' уже БЫЛ успешно завершен ранее!",
        "addendum_prefix": "\n✍️ [Дополнение]: ",
        "other_timer_running": "Запущен таймер на другом курсе.",
        "history_title": "**Журнал уроков:**",
        "history_empty": "История пуста.",
        "lesson_status_done": "✅ Завершен",
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
        "tab_active": "🚀 Active Courses",
        "tab_completed": "📦 Completed (Archive)",
        "folder_empty": "This folder is currently empty.",
        "course_stats": "⏱️ Study time: **{} hrs** | Unique lessons completed: **{} of {}**",
        "progress_label": "Progress: **{}%**",
        "manage_course": "🗑️ Manage Course",
        "delete_warn": "Delete '{}'?",
        "delete_confirm": "Yes, delete permanently",
        "exp_active_title": "⏳ SESSION IN PROGRESS! (Click to stop)",
        "exp_inactive_title": "⚡ Session & Lesson History",
        "archive_msg": "🎉 This course is fully completed! Only history viewing is available.",
        "btn_start": "⏱️ Start Session",
        "timer_running": "Timer running. Minutes passed: {}",
        "lesson_title_lbl": "Lesson title:",
        "lesson_placeholder": "e.g., Lesson 1",
        "comment_lbl": "What did you cover? (comment):",
        "mood_lbl": "Your mood:",
        "mood_options": ["🔥 Pumped / Got everything", "🟢 Good / Moving forward", "🟡 Normal / A bit tough", "🔴 Tired / Understood nothing"],
        "is_done_lbl": "✅ Is this lesson fully completed?",
        "btn_stop": "🛑 End Session",
        "err_format": "🛑 ERROR: Please use format 'Lesson X' (e.g., Lesson 1, Lesson 2).",
        "err_max_lessons": "🛑 ERROR: Only {} lessons are planned for this course!",
        "err_already_done": "🛑 ERROR: '{}' was ALREADY successfully completed before!",
        "addendum_prefix": "\n✍️ [Addendum]: ",
        "other_timer_running": "Timer is running on another course.",
        "history_title": "**Lesson log:**",
        "history_empty": "History is empty.",
        "lesson_status_done": "✅ Completed",
        "lesson_status_progress": "⏳ In progress",
        "min_label": "min.",
        "hist_total_time": "⏱️ `Total lesson time:` **{} min.** | `🧠 Mood:` {}",
        "hist_last_update": "📅 `Last update:` {}",
        "hist_notes": "💬 `Notes / Comments:`",
        "btn_del_lesson": "🗑️ Delete lesson",
        "sidebar_theme": "🎨 Interface Settings",
        "bg_color_label": "Background Color",
        "text_color_label": "Text Color"
    }
}

# === НАСТРОЙКА БАЗЫ ДАННЫХ ===
def get_db_connection():
    return psycopg2.connect(st.secrets["postgres"]["url"])

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS courses 
                 (id SERIAL PRIMARY KEY, name TEXT, total_lessons INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lessons 
                 (id SERIAL PRIMARY KEY, course_id INTEGER, 
                  lesson_name TEXT, duration_mins INTEGER, comment TEXT, mood TEXT, date TEXT, is_completed INTEGER DEFAULT 1)''')
    conn.commit()
    c.close()
    conn.close()

# === ИНИЦИАЛИЗАЦИЯ СТРИМЛИТА ===
init_db()
st.set_page_config(page_title="My Study Tracker", page_icon="🎓", layout="wide")

# ==========================================================
# 2. ПЕРЕКЛЮЧАТЕЛИ И КАСТОМИЗАЦИЯ В SIDEBAR
# ==========================================================
# Добавлен ключ key, чтобы выбор языка не сбрасывал состояние других виджетов
lang_choice = st.sidebar.selectbox("Language / Язык", ["RU", "EN"], key="persistent_lang")
t = LANGUAGES[lang_choice]

st.sidebar.markdown("---")
st.sidebar.header(t["sidebar_theme"])

# ИСПРАВЛЕНИЕ: Цвета теперь читаются из URL и привязываются к постоянным key, чтобы не слетать
initial_bg = st.query_params.get("bg_color", "#ffffff")
initial_text = st.query_params.get("text_color", "#1a1a1a")

bg_color = st.sidebar.color_picker(t["bg_color_label"], value=initial_bg, key="persistent_bg")
text_color = st.sidebar.color_picker(t["text_color_label"], value=initial_text, key="persistent_text")

st.query_params["bg_color"] = bg_color
st.query_params["text_color"] = text_color

# ==========================================================
# 3. МАГИЯ CSS (Цвета интерфейса + Скрытие подсказки ввода)
# ==========================================================
custom_css = f"""
<style>
    /* Меняем основной фон */
    .stApp {{
        background-color: {bg_color} !important;
    }}
    /* Красим весь текст, заголовки, списки и метрики */
    .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, label, .stSelectbox {{
        color: {text_color} !important;
    }}
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] {{
        color: {text_color} !important;
    }}
    /* Полностью убираем надпись 'Press enter to submit form' */
    div[data-testid="stFormSubmissionHint"] {{
        display: none !important;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# === SESSION STATE ===
if "active_course_id" not in st.session_state:
    st.session_state.active_course_id = None
if "start_time" not in st.session_state:
    st.session_state.start_time = None

st.title(t["title"])

conn = get_db_connection()
c = conn.cursor()

# Метрики для дашборда
c.execute("SELECT COUNT(*) FROM courses")
total_courses = c.fetchone()[0]

c.execute("SELECT SUM(duration_mins) FROM lessons")
total_hours = c.fetchone()[0] or 0
total_hours = round(total_hours / 60, 1)

col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric(t["metric_courses"], total_courses)
with col_m2:
    st.metric(t["metric_hours"], total_hours)

st.markdown("---")

# === SIDEBAR: ДОБАВЛЕНИЕ КУРСА ===
st.sidebar.header(t["sb_header"])
with st.sidebar.form("add_course_form", clear_on_submit=True):
    new_course_name = st.text_input(t["sb_course_name"], placeholder=t["sb_placeholder"])
    new_course_lessons = st.number_input(t["sb_lessons_count"], min_value=1, value=10, step=1)
    submit_course = st.form_submit_button(t["sb_submit"])
    
    if submit_course and new_course_name:
        c.execute("INSERT INTO courses (name, total_lessons) VALUES (%s, %s)", (new_course_name.strip(), new_course_lessons))
        conn.commit()
        st.sidebar.success(t["sb_success"].format(new_course_name))
        st.rerun()

# === СОРТИРОВКА ПО ПАПКАМ ===
# ИСПРАВЛЕНИЕ: Добавлена сортировка ORDER BY id DESC, чтобы новые курсы были вверху без ошибки отсутствия колонки даты
c.execute("SELECT id, name, total_lessons FROM courses ORDER BY id DESC")
all_courses = c.fetchall()
active_list = []
completed_list = []

for course in all_courses:
    c_id, c_name, t_lessons = course
    c.execute("""SELECT COUNT(*) FROM lessons 
                 WHERE course_id = %s AND is_completed = 1""", (c_id,))
    comp_lessons = c.fetchone()[0]
    if t_lessons > 0 and comp_lessons >= t_lessons:
        completed_list.append((course, comp_lessons))
    else:
        active_list.append((course, comp_lessons))

tab_active, tab_completed = st.tabs([t["tab_active"], t["tab_completed"]])

# === ОТРИСОВКА КУРСОВ ===
def render_courses(course_data_list, is_archive=False):
    if not course_data_list:
        st.info(t["folder_empty"])
        return

    local_conn = get_db_connection()
    local_c = local_conn.cursor()

    for i in range(0, len(course_data_list), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(course_data_list):
                (course_id, course_name, total_lessons), completed_lessons = course_data_list[i + j]
                
                progress_pct = min(int((completed_lessons / total_lessons) * 100), 100) if total_lessons > 0 else 0
                
                local_c.execute("SELECT SUM(duration_mins) FROM lessons WHERE course_id = %s", (course_id,))
                course_mins = local_c.fetchone()[0] or 0
                
                with cols[j]:
                    st.subheader(f"📘 {course_name}")
                    st.write(t["course_stats"].format(round(course_mins/60, 1), completed_lessons, total_lessons))
                    st.progress(progress_pct / 100)
                    st.write(t["progress_label"].format(progress_pct))
                    
                    with st.popover(t["manage_course"]):
                        st.warning(t["delete_warn"].format(course_name))
                        if st.button(t["delete_confirm"], key=f"del_course_{course_id}"):
                            local_c.execute("DELETE FROM courses WHERE id = %s", (course_id,))
                            local_c.execute("DELETE FROM lessons WHERE course_id = %s", (course_id,))
                            local_conn.commit()
                            st.rerun()

                    is_active = (st.session_state.active_course_id == course_id)
                    expander_title = t["exp_active_title"] if is_active else t["exp_inactive_title"]
                        
                    with st.expander(expander_title, expanded=is_active):
                        if is_archive:
                            st.success(t["archive_msg"])
                        else:
                            if st.session_state.active_course_id is None:
                                if st.button(t["btn_start"], key=f"start_{course_id}"):
                                    st.session_state.active_course_id = course_id
                                    st.session_state.start_time = time.time()
                                    st.rerun()
                            
                            elif st.session_state.active_course_id == course_id:
                                current_duration = int((time.time() - st.session_state.start_time) / 60)
                                st.warning(t["timer_running"].format(current_duration))
                                
                                with st.form(key=f"stop_form_{course_id}"):
                                    lesson_title = st.text_input(t["lesson_title_lbl"], placeholder=t["lesson_placeholder"]).strip()
                                    comment = st.text_area(t["comment_lbl"])
                                    mood = st.select_slider(t["mood_lbl"], options=t["mood_options"])
                                    is_done = st.checkbox(t["is_done_lbl"], value=True)
                                    
                                    submit_lesson = st.form_submit_button(t["btn_stop"])
                                    
                                    if submit_lesson:
                                        # Регулярка теперь поддерживает и "Урок", и "Lesson"
                                        match = re.match(r'(?i)^(?:урок\s*|lesson\s*)?(\d+)$', lesson_title)
                                        
                                        if not match:
                                            st.error(t["err_format"])
                                        else:
                                            lesson_num = int(match.group(1))
                                            
                                            if lesson_num < 1 or lesson_num > total_lessons:
                                                st.error(t["err_max_lessons"].format(total_lessons))
                                            else:
                                                # Приводим к красивому виду в зависимости от языка
                                                standardized_title = f"Lesson {lesson_num}" if lang_choice == "EN" else f"Урок {lesson_num}"
                                                
                                                # Проверяем на дубликаты (ищет обе языковые версии на всякий случай)
                                                local_c.execute("""SELECT COUNT(*) FROM lessons 
                                                                   WHERE course_id = %s AND (lesson_name = %s OR lesson_name = %s) AND is_completed = 1""", 
                                                                (course_id, f"Урок {lesson_num}", f"Lesson {lesson_num}"))
                                                already_done = local_c.fetchone()[0]
                                                
                                                if already_done > 0:
                                                    st.error(t["err_already_done"].format(standardized_title))
                                                else:
                                                    end_time = time.time()
                                                    duration = max(1, int((end_time - st.session_state.start_time) / 60))
                                                    today_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                                                    is_completed_val = 1 if is_done else 0
                                                    
                                                    local_c.execute("""SELECT id, duration_mins, comment FROM lessons 
                                                                       WHERE course_id = %s AND (lesson_name = %s OR lesson_name = %s) AND is_completed = 0""", 
                                                                    (course_id, f"Урок {lesson_num}", f"Lesson {lesson_num}"))
                                                    existing_incomplete = local_c.fetchone()
                                                    
                                                    if existing_incomplete:
                                                        sess_id, old_dur, old_comm = existing_incomplete
                                                        new_dur = old_dur + duration
                                                        
                                                        if old_comm and comment.strip():
                                                            combined_comment = f"{old_comm}{t['addendum_prefix']}{comment.strip()}"
                                                        elif comment.strip():
                                                            combined_comment = comment.strip()
                                                        else:
                                                            combined_comment = old_comm
                                                        
                                                        local_c.execute("""UPDATE lessons 
                                                                           SET duration_mins = %s, comment = %s, mood = %s, date = %s, is_completed = %s, lesson_name = %s
                                                                           WHERE id = %s""", 
                                                                        (new_dur, combined_comment, mood, today_date, is_completed_val, standardized_title, sess_id))
                                                    else:
                                                        local_c.execute("""INSERT INTO lessons (course_id, lesson_name, duration_mins, comment, mood, date, is_completed) 
                                                                           VALUES (%s, %s, %s, %s, %s, %s, %s)""", 
                                                                        (course_id, standardized_title, duration, comment.strip(), mood, today_date, is_completed_val))
                                                    
                                                    local_conn.commit()
                                                    st.session_state.active_course_id = None
                                                    st.session_state.start_time = None
                                                    st.rerun()
                            else:
                                st.info(t["other_timer_running"])
                        
                        st.markdown("---")
                        st.markdown(t["history_title"])
                        
                        local_c.execute("""SELECT id, lesson_name, duration_mins, comment, mood, date, is_completed 
                                           FROM lessons WHERE course_id = %s ORDER BY id DESC""", (course_id,))
                        lessons_history = local_c.fetchall()
                        
                        if not lessons_history:
                            st.caption(t["history_empty"])
                        else:
                            for sess_id, l_name, h_dur, h_comm, h_mood, h_date, h_comp in lessons_history:
                                status_label = t["lesson_status_done"] if h_comp == 1 else t["lesson_status_progress"]
                                
                                with st.expander(f"📘 {l_name} — {h_dur} {t['min_label']} ({status_label})"):
                                    col_sess_text, col_sess_del = st.columns([4, 1])
                                    with col_sess_text:
                                        st.markdown(t["hist_total_time"].format(h_dur, h_mood))
                                        st.markdown(t["hist_last_update"].format(h_date))
                                        if h_comm:
                                            st.markdown(t["hist_notes"])
                                            st.info(h_comm)
                                            
                                    with col_sess_del:
                                        if st.button(t["btn_del_lesson"], key=f"del_sess_{sess_id}"):
                                            local_c.execute("DELETE FROM lessons WHERE id = %s", (sess_id,))
                                            local_conn.commit()
                                            st.rerun()
                    st.write("")
    local_c.close()
    local_conn.close()

with tab_active:
    render_courses(active_list, is_archive=False)

with tab_completed:
    render_courses(completed_list, is_archive=True)

c.close()
conn.close()
