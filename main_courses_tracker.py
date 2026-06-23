import streamlit as st
import psycopg2
import time
import re
from datetime import datetime

# === НАСТРОЙКА БАЗЫ ДАННЫХ ===
def get_db_connection():
    # Берем URI подключения из секретов Streamlit
    return psycopg2.connect(st.secrets["postgres"]["url"])

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # В PostgreSQL используется SERIAL PRIMARY KEY вместо AUTOINCREMENT
    c.execute('''CREATE TABLE IF NOT EXISTS courses 
                 (id SERIAL PRIMARY KEY, name TEXT, total_lessons INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lessons 
                 (id SERIAL PRIMARY KEY, course_id INTEGER, 
                  lesson_name TEXT, duration_mins INTEGER, comment TEXT, mood TEXT, date TEXT, is_completed INTEGER DEFAULT 1)''')
    conn.commit()
    c.close()
    conn.close()

# === ИНИЦИАЛИЗАЦИЯ ===
init_db()
st.set_page_config(page_title="Мой Трекер Обучения", page_icon="🎓", layout="wide")

if "active_course_id" not in st.session_state:
    st.session_state.active_course_id = None
if "start_time" not in st.session_state:
    st.session_state.start_time = None

st.title("🎓 Персональный трекер обучения")

conn = get_db_connection()
c = conn.cursor()

# Метрики для дашборда (в psycopg2 метод execute не возвращает сам курсор, чейнинг запрещен)
c.execute("SELECT COUNT(*) FROM courses")
total_courses = c.fetchone()[0]

c.execute("SELECT SUM(duration_mins) FROM lessons")
total_hours = c.fetchone()[0] or 0
total_hours = round(total_hours / 60, 1)

col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric("Всего курсов в базе", total_courses)
with col_m2:
    st.metric("Общее время в учебе (часы)", total_hours)

st.markdown("---")

# === БОКОВАЯ ПАНЕЛЬ ===
st.sidebar.header("➕ Добавить новый курс")
with st.sidebar.form("add_course_form", clear_on_submit=True):
    new_course_name = st.text_input("Название курса:", placeholder="например, CS50 Python")
    new_course_lessons = st.number_input("Количество уроков в курсе:", min_value=1, value=10, step=1)
    submit_course = st.form_submit_button("Создать отслеживание")
    
    if submit_course and new_course_name:
        c.execute("INSERT INTO courses (name, total_lessons) VALUES (%s, %s)", (new_course_name.strip(), new_course_lessons))
        conn.commit()
        st.sidebar.success(f"Курс '{new_course_name}' успешно добавлен!")
        st.rerun()

# === СОРТИРОВКА ПО ПАПКАМ ===
c.execute("SELECT id, name, total_lessons FROM courses")
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

tab_active, tab_completed = st.tabs(["🚀 Активные курсы", "📦 Пройденные (Архив)"])

def render_courses(course_data_list, is_archive=False):
    if not course_data_list:
        st.info("В этой папке пока ничего нет.")
        return

    # Пересоздаем курсор внутри функции, чтобы избежать конфликтов
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
                    st.write(f"⏱️ Налетано: **{round(course_mins/60, 1)} ч.** | Пройдено уникальных уроков: **{completed_lessons} из {total_lessons}**")
                    st.progress(progress_pct / 100)
                    st.write(f"Прогресс: **{progress_pct}%**")
                    
                    with st.popover("🗑️ Управление курсом"):
                        st.warning(f"Удалить '{course_name}'?")
                        if st.button("Да, удалить окончательно", key=f"del_course_{course_id}"):
                            local_c.execute("DELETE FROM courses WHERE id = %s", (course_id,))
                            local_c.execute("DELETE FROM lessons WHERE course_id = %s", (course_id,))
                            local_conn.commit()
                            st.rerun()

                    is_active = (st.session_state.active_course_id == course_id)
                    expander_title = "⏳ ИДЕТ ЗАНЯТИЕ! (Нажмите для остановки)" if is_active else "⚡ Занятие и История уроков"
                        
                    with st.expander(expander_title, expanded=is_active):
                        if is_archive:
                            st.success("🎉 Этот курс полностью пройден! Доступен только просмотр истории.")
                        else:
                            if st.session_state.active_course_id is None:
                                if st.button("⏱️ Начать занятие", key=f"start_{course_id}"):
                                    st.session_state.active_course_id = course_id
                                    st.session_state.start_time = time.time()
                                    st.rerun()
                            
                            elif st.session_state.active_course_id == course_id:
                                current_duration = int((time.time() - st.session_state.start_time) / 60)
                                st.warning(f"Таймер запущен. Прошло минут: {current_duration}")
                                
                                with st.form(key=f"stop_form_{course_id}"):
                                    lesson_title = st.text_input("Название урока:", placeholder="например, Урок 1").strip()
                                    comment = st.text_area("Что прошли? (комментарий):")
                                    mood = st.select_slider("Ваше настроение:", 
                                                           options=["🔥 Заряжен / Все понял", "🟢 Хорошо / Двигаюсь дальше", "🟡 Нормально / Сложновато", "🔴 Устал / Ничего не понял"])
                                    is_done = st.checkbox("✅ Этот урок полностью завершен?", value=True)
                                    
                                    submit_lesson = st.form_submit_button("🛑 Завершить сессию")
                                    
                                    if submit_lesson:
                                        match = re.match(r'(?i)^(?:урок\s*)?(\d+)$', lesson_title)
                                        
                                        if not match:
                                            st.error("🛑 ОШИБКА: Пожалуйста, используйте формат 'Урок X' (например: Урок 1, Урок 2).")
                                        else:
                                            lesson_num = int(match.group(1))
                                            
                                            if lesson_num < 1 or lesson_num > total_lessons:
                                                st.error(f"🛑 ОШИБКА: В этом курсе запланировано всего {total_lessons} уроков!")
                                            else:
                                                standardized_title = f"Урок {lesson_num}"
                                                
                                                local_c.execute("""SELECT COUNT(*) FROM lessons 
                                                                   WHERE course_id = %s AND lesson_name = %s AND is_completed = 1""", 
                                                                (course_id, standardized_title))
                                                already_done = local_c.fetchone()[0]
                                                
                                                if already_done > 0:
                                                    st.error(f"🛑 ОШИБКА: '{standardized_title}' уже БЫЛ успешно завершен ранее!")
                                                else:
                                                    end_time = time.time()
                                                    duration = max(1, int((end_time - st.session_state.start_time) / 60))
                                                    today_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                                                    is_completed_val = 1 if is_done else 0
                                                    
                                                    local_c.execute("""SELECT id, duration_mins, comment FROM lessons 
                                                                       WHERE course_id = %s AND lesson_name = %s AND is_completed = 0""", 
                                                                    (course_id, standardized_title))
                                                    existing_incomplete = local_c.fetchone()
                                                    
                                                    if existing_incomplete:
                                                        sess_id, old_dur, old_comm = existing_incomplete
                                                        new_dur = old_dur + duration
                                                        
                                                        if old_comm and comment.strip():
                                                            combined_comment = f"{old_comm}\n✍️ [Дополнение]: {comment.strip()}"
                                                        elif comment.strip():
                                                            combined_comment = comment.strip()
                                                        else:
                                                            combined_comment = old_comm
                                                        
                                                        local_c.execute("""UPDATE lessons 
                                                                           SET duration_mins = %s, comment = %s, mood = %s, date = %s, is_completed = %s 
                                                                           WHERE id = %s""", 
                                                                        (new_dur, combined_comment, mood, today_date, is_completed_val, sess_id))
                                                    else:
                                                        local_c.execute("""INSERT INTO lessons (course_id, lesson_name, duration_mins, comment, mood, date, is_completed) 
                                                                           VALUES (%s, %s, %s, %s, %s, %s, %s)""", 
                                                                        (course_id, standardized_title, duration, comment.strip(), mood, today_date, is_completed_val))
                                                    
                                                    local_conn.commit()
                                                    st.session_state.active_course_id = None
                                                    st.session_state.start_time = None
                                                    st.rerun()
                            else:
                                st.info("Запущен таймер на другом курсе.")
                        
                        st.markdown("---")
                        st.markdown("**Журнал уроков:**")
                        
                        local_c.execute("""SELECT id, lesson_name, duration_mins, comment, mood, date, is_completed 
                                           FROM lessons WHERE course_id = %s ORDER BY id DESC""", (course_id,))
                        lessons_history = local_c.fetchall()
                        
                        if not lessons_history:
                            st.caption("История пуста.")
                        else:
                            for sess_id, l_name, h_dur, h_comm, h_mood, h_date, h_comp in lessons_history:
                                status_label = "✅ Завершен" if h_comp == 1 else "⏳ В процессе"
                                
                                with st.expander(f"📘 {l_name} — {h_dur} мин. ({status_label})"):
                                    col_sess_text, col_sess_del = st.columns([4, 1])
                                    with col_sess_text:
                                        st.markdown(f"⏱️ `Общее время урока:` **{h_dur} мин.** | `🧠 Настроение:` {h_mood}")
                                        st.markdown(f"📅 `Последнее обновление:` {h_date}")
                                        if h_comm:
                                            st.markdown("💬 `Заметки / Комментарии:`")
                                            st.info(h_comm)
                                            
                                    with col_sess_del:
                                        if st.button("🗑️ Удалить урок", key=f"del_sess_{sess_id}"):
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