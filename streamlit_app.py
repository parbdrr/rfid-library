import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re
import json
from pathlib import Path
import sqlite3
import time
import random

# Database setup
def init_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            book_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'Available'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            books_issued INTEGER DEFAULT 0
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            book_id TEXT,
            student_id TEXT,
            rfid TEXT NOT NULL,
            issue_date TIMESTAMP NOT NULL,
            due_date TIMESTAMP NOT NULL,
            return_date TIMESTAMP,
            status TEXT DEFAULT 'Issued',
            fee REAL DEFAULT 0.0,
            FOREIGN KEY (book_id) REFERENCES books (book_id),
            FOREIGN KEY (student_id) REFERENCES students (student_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    try:
        conn = sqlite3.connect('library.db')
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    except sqlite3.Error as e:
        st.error(f"Database connection error: {str(e)}")
        return None

# Page Configuration
st.set_page_config(
    page_title="Library Management System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    /* Base theme */
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
    }
    
    /* Components */
    .stButton>button {
        background-color: #ff0000;
        color: white;
        border: none;
        padding: 0.7rem 1.5rem;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        width: 100%;
    }
    
    .stButton>button:hover {
        background-color: #cc0000;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(255, 0, 0, 0.3);
    }
    
    /* Input fields */
    .stTextInput>div>div>input,
    .stSelectbox>div>div {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 2px solid #333333 !important;
        border-radius: 6px !important;
        padding: 0.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div:focus {
        border-color: #ff0000 !important;
        box-shadow: 0 0 0 2px rgba(255, 0, 0, 0.2) !important;
    }
    
    /* Tables */
    .dataframe {
        background-color: #1a1a1a !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        width: 100% !important;
    }
    
    .dataframe th {
        background-color: #0a0a0a !important;
        color: #ff0000 !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        border-bottom: 2px solid #333333 !important;
        text-align: left !important;
    }
    
    .dataframe td {
        background-color: #1a1a1a !important;
        color: white !important;
        padding: 0.8rem 1rem !important;
        border-bottom: 1px solid #333333 !important;
        text-align: left !important;
    }
    
    .dataframe tr:hover td {
        background-color: #222222 !important;
    }
    
    /* Cards and containers */
    .metric-card {
        background-color: #1a1a1a;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(255, 0, 0, 0.2);
        border-color: #ff0000;
    }
    
    /* Search container */
    .search-container {
        background-color: #1a1a1a;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border: 1px solid #333333;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Stats card */
    .stats-card {
        background-color: #1a1a1a;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #0a0a0a;
    }
    
    .css-1d391kg .stButton>button {
        width: 100%;
    }
    
    /* Alerts and messages */
    .stAlert, .stInfo, .stSuccess, .stError {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        border-bottom: 2px solid #333333;
        padding-bottom: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1a1a;
        color: white;
        border-radius: 6px;
        transition: all 0.3s ease;
        padding: 0.8rem 1.5rem;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ff0000;
        color: white;
        font-weight: 600;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(255, 0, 0, 0.2);
    }
    
    /* Forms */
    .stForm {
        background-color: #1a1a1a;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 1rem !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #ff0000 !important;
    }
    
    /* Footer */
    .footer {
        background-color: #0a0a0a;
        border-top: 1px solid #333333;
        padding: 1.5rem 0;
        margin-top: 2rem;
        text-align: center;
    }
    
    /* Status badges */
    .status-ok {
        background-color: #1a472a !important;
        color: #4caf50 !important;
        padding: 6px 12px !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .status-warning {
        background-color: #4a3c00 !important;
        color: #ffd700 !important;
        padding: 6px 12px !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .status-blocked {
        background-color: #4a0000 !important;
        color: #ff4444 !important;
        padding: 6px 12px !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* RFID Scanner */
    .rfid-container {
        background-color: #1a1a1a;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #333333;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Add greeting
st.markdown("""
    <div class="greeting">
        Hello Medha ma'am! 👋
    </div>
""", unsafe_allow_html=True)

# Data Classes
class Book:
    def __init__(self, book_id, title, author, isbn, category, status='Available'):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.isbn = isbn
        self.category = category
        self.status = status

class Student:
    def __init__(self, student_id, name, email, phone, books_issued=0):
        self.student_id = student_id
        self.name = name
        self.email = email
        self.phone = phone
        self.books_issued = books_issued
        self.transactions = []

class Transaction:
    def __init__(self, transaction_id, book_id, student_id, rfid, issue_date, due_date, return_date=None, status='Issued', fee=0.0):
        self.transaction_id = transaction_id
        self.book_id = book_id
        self.student_id = student_id
        self.rfid = rfid
        self.issue_date = issue_date
        self.due_date = due_date
        self.return_date = return_date
        self.status = status
        self.fee = fee

# Initialize session state
if 'books' not in st.session_state:
    st.session_state.books = []
if 'students' not in st.session_state:
    st.session_state.students = []
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

def render_header():
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0; background-color: #1a1a1a; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(255, 0, 0, 0.2);'>
            <h1 style='color: #ff0000; font-size: 3.5rem; margin-bottom: 0.5rem; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);'>PAAD LIBRARY</h1>
            <p style='color: #ffffff; font-size: 1.2rem; opacity: 0.9; letter-spacing: 1px;'>Professional RFID-Based Library Management System</p>
            <div style='margin-top: 1rem; padding: 0.5rem; background-color: #0a0a0a; border-radius: 6px; display: inline-block;'>
                <p style='color: #ff0000; font-size: 1rem; margin: 0; font-weight: 600;'>📚 Knowledge is Power 📚</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_metrics():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get total books
    c.execute('SELECT COUNT(*) FROM books')
    total_books = c.fetchone()[0]
    
    # Get total students
    c.execute('SELECT COUNT(*) FROM students')
    total_students = c.fetchone()[0]
    
    # Get active issues
    c.execute('SELECT COUNT(*) FROM transactions WHERE status = "Issued"')
    active_issues = c.fetchone()[0]
    
    # Get overdue books
    c.execute('''
        SELECT COUNT(*) FROM transactions 
        WHERE status = "Issued" AND due_date < datetime('now')
    ''')
    overdue_books = c.fetchone()[0]
    
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <h3 style='color: #ffffff; margin-bottom: 0.5rem; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px;'>📚 Total Books</h3>
                <p style='font-size: 2.2rem; font-weight: 700; color: #ff0000;'>{total_books}</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class='metric-card'>
                <h3 style='color: #ffffff; margin-bottom: 0.5rem; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px;'>👥 Total Students</h3>
                <p style='font-size: 2.2rem; font-weight: 700; color: #ff0000;'>{total_students}</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class='metric-card'>
                <h3 style='color: #ffffff; margin-bottom: 0.5rem; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px;'>📖 Active Issues</h3>
                <p style='font-size: 2.2rem; font-weight: 700; color: #ff0000;'>{active_issues}</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class='metric-card'>
                <h3 style='color: #ffffff; margin-bottom: 0.5rem; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px;'>⏰ Overdue Books</h3>
                <p style='font-size: 2.2rem; font-weight: 700; color: #ff0000;'>{overdue_books}</p>
            </div>
        """, unsafe_allow_html=True)

def render_forms():
    st.sidebar.markdown("### 📝 Quick Actions")
    
    with st.sidebar.expander("➕ Add New Book", expanded=False):
        with st.form("add_book_form"):
            st.markdown("#### Add New Book")
            book_id = st.text_input("Book ID (3 digits)")
            title = st.text_input("Book Title")
            author = st.text_input("Author")
            isbn = st.text_input("ISBN")
            category = st.selectbox(
                "Category",
                ["Fiction", "Non-Fiction", "Science", "Technology", "History", "Biography", "Other"]
            )
            if st.form_submit_button("Add Book"):
                if add_book(book_id, title, author, isbn, category):
                    st.success("✅ Book added successfully!")
    
    with st.sidebar.expander("➕ Add New Student", expanded=False):
        with st.form("add_student_form"):
            st.markdown("#### Add New Student")
            student_id = st.text_input("Student ID (8 alphanumeric)")
            name = st.text_input("Student Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            if st.form_submit_button("Add Student"):
                if add_student(student_id, name, email, phone):
                    st.success("✅ Student added successfully!")
    
    with st.sidebar.expander("📖 Issue Book", expanded=False):
        with st.form("issue_book_form"):
            st.markdown("#### Issue Book")
            book_id = st.text_input("Book ID")
            student_id = st.text_input("Student ID")
            rfid = st.text_input("RFID Tag")
            if st.form_submit_button("Issue Book"):
                if issue_book(book_id, student_id, rfid):
                    st.success("✅ Book issued successfully!")
    
    with st.sidebar.expander("📥 Return Book", expanded=False):
        with st.form("return_book_form"):
            st.markdown("#### Return Book")
            book_id = st.text_input("Book ID")
            student_id = st.text_input("Student ID")
            if st.form_submit_button("Return Book"):
                if return_book(book_id, student_id):
                    st.success("✅ Book returned successfully!")

def render_tables():
    tab1, tab2, tab3 = st.tabs(["📚 Books", "👥 Students", "📖 Transactions"])
    
    conn = get_db_connection()
    if not conn:
        st.error("Failed to connect to database")
        return
        
    c = conn.cursor()
    
    try:
        with tab1:
            c.execute('SELECT * FROM books')
            books = c.fetchall()
            if books:
                books_df = pd.DataFrame(books, columns=['book_id', 'title', 'author', 'isbn', 'category', 'status'])
                st.dataframe(
                    books_df.style.apply(
                        lambda x: ['background-color: #ff0000; color: #ffffff;' if v == 'Issued' else '' for v in x],
                        axis=1
                    ),
                    use_container_width=True
                )
            else:
                st.info("No books in the library yet.")
        
        with tab2:
            c.execute('''
                SELECT 
                    s.student_id,
                    s.name,
                    s.email,
                    s.phone,
                    s.books_issued,
                    COUNT(t.transaction_id) as active_issues,
                    SUM(CASE WHEN t.status = 'Issued' AND t.due_date < datetime('now') THEN 1 ELSE 0 END) as overdue_books,
                    MAX(CASE WHEN t.status = 'Issued' AND t.due_date < datetime('now') 
                        THEN julianday('now') - julianday(t.due_date) ELSE 0 END) as max_overdue_days,
                    SUM(CASE WHEN t.status = 'Issued' AND t.due_date < datetime('now') 
                        THEN (julianday('now') - julianday(t.due_date)) * 10 ELSE 0 END) as total_due_fee
                FROM students s
                LEFT JOIN transactions t ON s.student_id = t.student_id AND t.status = 'Issued'
                GROUP BY s.student_id
            ''')
            students = c.fetchall()
            
            if students:
                students_data = []
                for student in students:
                    # Get current books for this student
                    c.execute('''
                        SELECT b.title, t.issue_date, t.due_date, t.fee
                        FROM transactions t
                        JOIN books b ON t.book_id = b.book_id
                        WHERE t.student_id = ? AND t.status = 'Issued'
                    ''', (student['student_id'],))
                    current_books = c.fetchall()
                    
                    library_status = 'OK'
                    if student['max_overdue_days'] > 14:
                        library_status = 'Blocked'
                    elif student['overdue_books'] > 0:
                        library_status = 'Warning'
                    
                    current_books_list = []
                    issue_dates = []
                    due_dates = []
                    book_fees = []
                    
                    for book in current_books:
                        current_books_list.append(book['title'])
                        # Format dates
                        try:
                            issue_date = datetime.strptime(book['issue_date'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d-%m-%Y')
                            due_date = datetime.strptime(book['due_date'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d-%m-%Y')
                        except:
                            issue_date = book['issue_date']
                            due_date = book['due_date']
                        
                        issue_dates.append(issue_date)
                        due_dates.append(due_date)
                        book_fees.append(f"₹{float(book['fee']):.2f}" if book['fee'] else "₹0.00")
                    
                    students_data.append({
                        'student_id': student['student_id'],
                        'name': student['name'],
                        'email': student['email'],
                        'phone': student['phone'],
                        'books_issued': student['books_issued'],
                        'current_books': '\n'.join(current_books_list) if current_books_list else 'No books issued',
                        'issue_dates': '\n'.join(issue_dates) if issue_dates else 'N/A',
                        'due_dates': '\n'.join(due_dates) if due_dates else 'N/A',
                        'book_fees': '\n'.join(book_fees) if book_fees else 'N/A',
                        'overdue_books': student['overdue_books'],
                        'max_overdue_days': int(student['max_overdue_days']),
                        'library_status': library_status,
                        'total_due_fee': f"₹{float(student['total_due_fee']):.2f}" if student['total_due_fee'] else "₹0.00"
                    })
                
                students_df = pd.DataFrame(students_data)
                st.dataframe(
                    students_df.style.applymap(
                        lambda x: 'background-color: #4a0000; color: #ff4444;' if x == 'Blocked'
                        else 'background-color: #4a3c00; color: #ffd700;' if x == 'Warning'
                        else 'background-color: #1a472a; color: #4caf50;',
                        subset=['library_status']
                    ),
                    use_container_width=True
                )
                
                st.markdown("""
                    <div style='background-color: #1a1a1a; border: 1px solid #ffd700; padding: 1rem; border-radius: 8px; margin-top: 1rem;'>
                        <h4 style='color: #ffd700; margin-bottom: 0.5rem;'>Status Legend:</h4>
                        <p style='color: #4caf50;'>🟢 OK - No overdue books</p>
                        <p style='color: #ffd700;'>🟠 Warning - Has overdue books</p>
                        <p style='color: #ff4444;'>🔴 Blocked - Overdue for more than 14 days</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No students registered yet.")
        
        with tab3:
            c.execute('''
                SELECT 
                    t.transaction_id,
                    t.book_id,
                    b.title as book_title,
                    t.student_id,
                    s.name as student_name,
                    t.rfid,
                    t.issue_date,
                    t.due_date,
                    t.return_date,
                    t.status,
                    t.fee
                FROM transactions t
                JOIN books b ON t.book_id = b.book_id
                JOIN students s ON t.student_id = s.student_id
                ORDER BY t.issue_date DESC
            ''')
            transactions = c.fetchall()
            
            if transactions:
                transactions_data = []
                for t in transactions:
                    # Convert dates to consistent format
                    try:
                        issue_date = datetime.strptime(t['issue_date'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d-%m-%Y')
                        due_date = datetime.strptime(t['due_date'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d-%m-%Y')
                        return_date = datetime.strptime(t['return_date'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d-%m-%Y') if t['return_date'] else None
                    except:
                        issue_date = t['issue_date']
                        due_date = t['due_date']
                        return_date = t['return_date']
                    
                    transactions_data.append({
                        'transaction_id': t['transaction_id'],
                        'book_id': t['book_id'],
                        'book_title': t['book_title'],
                        'student_id': t['student_id'],
                        'student_name': t['student_name'],
                        'rfid': t['rfid'],
                        'issue_date': issue_date,
                        'due_date': due_date,
                        'return_date': return_date,
                        'status': t['status'],
                        'fee': f"₹{float(t['fee']):.2f}" if t['fee'] else "₹0.00"
                    })
                
                transactions_df = pd.DataFrame(transactions_data)
                st.dataframe(
                    transactions_df.style.apply(
                        lambda x: ['background-color: #ff0000; color: #ffffff;' 
                                 if x['status'] == 'Issued' and pd.notnull(x['due_date']) 
                                 and datetime.strptime(x['due_date'], '%d-%m-%Y') < datetime.now() else '' 
                                 for _ in x],
                        axis=1
                    ),
                    use_container_width=True
                )
            else:
                st.info("No transactions recorded yet.")
    except Exception as e:
        st.error(f"Error displaying tables: {str(e)}")
    finally:
        conn.close()

def render_rfid_scanner():
    st.markdown("""
        <div class="rfid-container">
            <h3 style='color: #ff0000; margin-bottom: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>📱 RFID Scanner</h3>
            <p style='color: #ffffff; opacity: 0.9; margin-bottom: 1rem;'>Place the book near the scanner to read its RFID tag</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔍 Scan RFID", use_container_width=True):
        with st.spinner("Scanning..."):
            time.sleep(1)
            rfid = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
            st.session_state.current_rfid = rfid
            st.success(f"Scanned RFID: {rfid}")
    
    if 'current_rfid' in st.session_state:
        st.markdown(f"""
            <div style='background-color: #1a1a1a; padding: 1rem; border-radius: 8px; border: 1px solid #333333; margin-top: 1rem;'>
                <p style='color: #ffffff; margin: 0;'>
                    Current RFID: <strong style='color: #ff0000;'>{st.session_state.current_rfid}</strong>
                </p>
            </div>
        """, unsafe_allow_html=True)

def add_book(book_id, title, author, isbn, category):
    if not book_id or not title or not author or not isbn or not category:
        st.error("All fields are required!")
        return False
    
    if not book_id.isdigit() or len(book_id) != 3:
        st.error("Book ID must be 3 digits!")
        return False
    
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute('SELECT book_id FROM books WHERE book_id = ?', (book_id,))
        if c.fetchone():
            st.error("Book ID already exists!")
            return False
        
        c.execute('''
            INSERT INTO books (book_id, title, author, isbn, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (book_id, title, author, isbn, category))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding book: {str(e)}")
        return False
    finally:
        conn.close()

def add_student(student_id, name, email, phone):
    if not student_id or not name or not email or not phone:
        st.error("All fields are required!")
        return False
    
    if not re.match(r'^[A-Za-z0-9]{8}$', student_id):
        st.error("Student ID must be 8 alphanumeric characters!")
        return False
    
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute('SELECT student_id FROM students WHERE student_id = ?', (student_id,))
        if c.fetchone():
            st.error("Student ID already exists!")
            return False
        
        c.execute('''
            INSERT INTO students (student_id, name, email, phone)
            VALUES (?, ?, ?, ?)
        ''', (student_id, name, email, phone))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding student: {str(e)}")
        return False
    finally:
        conn.close()

def issue_book(book_id, student_id, rfid):
    if not book_id or not student_id or not rfid:
        st.error("All fields are required!")
        return False
    
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Check book availability
        c.execute('SELECT status FROM books WHERE book_id = ?', (book_id,))
        book = c.fetchone()
        if not book:
            st.error("Book not found!")
            return False
        if book[0] == 'Issued':
            st.error("Book is already issued!")
            return False
        
        # Check student's book limit
        c.execute('SELECT books_issued FROM students WHERE student_id = ?', (student_id,))
        student = c.fetchone()
        if not student:
            st.error("Student not found!")
            return False
        if student[0] >= 3:
            st.error("Student has reached maximum book limit!")
            return False
        
        # Create transaction
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=14)
        transaction_id = f"T{len(get_all_transactions()) + 1:03d}"
        
        c.execute('''
            INSERT INTO transactions 
            (transaction_id, book_id, student_id, rfid, issue_date, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (transaction_id, book_id, student_id, rfid, issue_date, due_date))
        
        # Update book and student status
        c.execute('UPDATE books SET status = ? WHERE book_id = ?', ('Issued', book_id))
        c.execute('UPDATE students SET books_issued = books_issued + 1 WHERE student_id = ?', (student_id,))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error issuing book: {str(e)}")
        return False
    finally:
        conn.close()

def return_book(book_id, student_id):
    if not book_id or not student_id:
        st.error("All fields are required!")
        return False
    
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Check book status
        c.execute('SELECT status FROM books WHERE book_id = ?', (book_id,))
        book = c.fetchone()
        if not book:
            st.error("Book not found!")
            return False
        if book[0] == 'Available':
            st.error("Book is already available!")
            return False
        
        # Check student
        c.execute('SELECT student_id FROM students WHERE student_id = ?', (student_id,))
        if not c.fetchone():
            st.error("Student not found!")
            return False
        
        # Get active transaction
        c.execute('''
            SELECT transaction_id, due_date 
            FROM transactions 
            WHERE book_id = ? AND student_id = ? AND status = 'Issued'
        ''', (book_id, student_id))
        transaction = c.fetchone()
        
        if not transaction:
            st.error("No active issue found for this book and student!")
            return False
        
        # Calculate fee
        return_date = datetime.now()
        due_date = datetime.strptime(transaction[1], '%Y-%m-%d %H:%M:%S.%f')
        days_overdue = (return_date - due_date).days if return_date > due_date else 0
        fee = days_overdue * 10
        
        # Update transaction
        c.execute('''
            UPDATE transactions 
            SET return_date = ?, status = 'Returned', fee = ?
            WHERE transaction_id = ?
        ''', (return_date, fee, transaction[0]))
        
        # Update book and student status
        c.execute('UPDATE books SET status = ? WHERE book_id = ?', ('Available', book_id))
        c.execute('UPDATE students SET books_issued = books_issued - 1 WHERE student_id = ?', (student_id,))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error returning book: {str(e)}")
        return False
    finally:
        conn.close()

def get_all_books():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM books')
    books = c.fetchall()
    conn.close()
    return books

def get_all_students():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM students')
    students = c.fetchall()
    conn.close()
    return students

def get_all_transactions():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM transactions')
    transactions = c.fetchall()
    conn.close()
    return transactions

def initialize_sample_data():
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # Check if data already exists
        c.execute('SELECT COUNT(*) FROM books')
        if c.fetchone()[0] > 0:
            return
        
        # Add sample books
        categories = ["Fiction", "Non-Fiction", "Science", "Technology", "History", "Biography", "Mathematics", "Physics", "Chemistry", "Biology", "Computer Science", "Literature", "Philosophy", "Psychology", "Economics"]
        authors = ["John Smith", "Jane Doe", "Robert Johnson", "Emily Brown", "Michael Wilson", "Sarah Davis", "David Miller", "Lisa Anderson", "James Taylor", "Mary Thomas"]
        
        for i in range(100):
            book_id = f"{i+1:03d}"
            title = f"Book {i+1}"
            author = random.choice(authors)
            isbn = f"978-{random.randint(1000000000, 9999999999)}"
            category = random.choice(categories)
            status = "Available" if random.random() > 0.3 else "Issued"
            
            c.execute('''
                INSERT INTO books (book_id, title, author, isbn, category, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (book_id, title, author, isbn, category, status))
        
        # Add sample students
        first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah", "James", "Lisa", "Robert", "Mary", "William", "Emma", "Daniel", "Sophia", "Matthew"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]
        
        for i in range(25):
            student_id = f"STU{i+1:03d}"
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            email = f"{name.lower().replace(' ', '.')}@example.com"
            phone = f"{random.randint(1000000000, 9999999999)}"
            books_issued = random.randint(0, 3)
            
            c.execute('''
                INSERT INTO students (student_id, name, email, phone, books_issued)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_id, name, email, phone, books_issued))
        
        # Add sample transactions
        for _ in range(50):
            c.execute('SELECT book_id FROM books WHERE status = "Issued" ORDER BY RANDOM() LIMIT 1')
            book = c.fetchone()
            if not book:
                continue
                
            c.execute('SELECT student_id FROM students ORDER BY RANDOM() LIMIT 1')
            student = c.fetchone()
            if not student:
                continue
            
            issue_date = datetime.now() - timedelta(days=random.randint(1, 30))
            due_date = issue_date + timedelta(days=14)
            return_date = None if random.random() > 0.5 else due_date + timedelta(days=random.randint(1, 10))
            status = "Issued" if return_date is None else "Returned"
            fee = 0 if return_date is None else max(0, (return_date - due_date).days * 10)
            
            transaction_id = f"T{_+1:03d}"
            rfid = f"RFID{random.randint(1000, 9999)}"
            
            c.execute('''
                INSERT INTO transactions 
                (transaction_id, book_id, student_id, rfid, issue_date, due_date, return_date, status, fee)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, book[0], student[0], rfid, issue_date, due_date, return_date, status, fee))
        
        conn.commit()
    except Exception as e:
        st.error(f"Error initializing sample data: {str(e)}")
    finally:
        conn.close()

def render_search():
    st.markdown("""
        <div class="search-container">
            <h3 style='color: #ff0000; margin-bottom: 1rem;'>🔍 Search Library</h3>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        search_type = st.selectbox("Search by", ["Books", "Students", "Transactions"])
    with col2:
        search_query = st.text_input("Enter search term")
    
    if search_query:
        conn = get_db_connection()
        c = conn.cursor()
        
        try:
            if search_type == "Books":
                c.execute('''
                    SELECT * FROM books 
                    WHERE LOWER(title) LIKE ? 
                    OR LOWER(author) LIKE ? 
                    OR book_id LIKE ?
                ''', (f'%{search_query.lower()}%', f'%{search_query.lower()}%', f'%{search_query}%'))
                results = c.fetchall()
                
                if results:
                    st.success(f"Found {len(results)} books")
                    books_df = pd.DataFrame(results, columns=['book_id', 'title', 'author', 'isbn', 'category', 'status'])
                    st.dataframe(books_df, use_container_width=True)
                else:
                    st.warning("No books found")
            
            elif search_type == "Students":
                c.execute('''
                    SELECT * FROM students 
                    WHERE LOWER(name) LIKE ? 
                    OR student_id LIKE ?
                ''', (f'%{search_query.lower()}%', f'%{search_query}%'))
                results = c.fetchall()
                
                if results:
                    st.success(f"Found {len(results)} students")
                    students_df = pd.DataFrame(results, columns=['student_id', 'name', 'email', 'phone', 'books_issued'])
                    st.dataframe(students_df, use_container_width=True)
                else:
                    st.warning("No students found")
            
            else:  # Transactions
                c.execute('''
                    SELECT * FROM transactions 
                    WHERE transaction_id LIKE ? 
                    OR book_id LIKE ? 
                    OR student_id LIKE ?
                ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
                results = c.fetchall()
                
                if results:
                    st.success(f"Found {len(results)} transactions")
                    transactions_df = pd.DataFrame(results, columns=['transaction_id', 'book_id', 'student_id', 'rfid', 'issue_date', 'due_date', 'return_date', 'status', 'fee'])
                    st.dataframe(transactions_df, use_container_width=True)
                else:
                    st.warning("No transactions found")
        finally:
            conn.close()

def render_stats():
    st.markdown("""
        <div class="stats-card">
            <h3 style='color: #ff0000; margin-bottom: 1rem;'>📊 Library Statistics</h3>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        with col1:
            # Category distribution
            c.execute('''
                SELECT category, COUNT(*) as count 
                FROM books 
                GROUP BY category 
                ORDER BY count DESC
            ''')
            categories = c.fetchall()
            
            st.markdown("#### Book Categories")
            for category, count in categories:
                st.markdown(f"""
                    <div style='background-color: #1a1a1a; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;'>
                        <span style='color: #ffffff;'>{category}:</span>
                        <span style='color: #ff0000; float: right;'>{count}</span>
                    </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Overdue books
            c.execute('''
                SELECT b.title, s.name, t.due_date
                FROM transactions t
                JOIN books b ON t.book_id = b.book_id
                JOIN students s ON t.student_id = s.student_id
                WHERE t.status = 'Issued' AND t.due_date < datetime('now')
            ''')
            overdue_books = c.fetchall()
            
            st.markdown("#### Overdue Books")
            if overdue_books:
                for title, name, due_date in overdue_books:
                    days_overdue = (datetime.now() - datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S.%f')).days
                    st.markdown(f"""
                        <div style='background-color: #1a1a1a; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;'>
                            <div style='color: #ffffff;'>{title}</div>
                            <div style='color: #ff0000; font-size: 0.9rem;'>
                                {name} - {days_overdue} days overdue
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("No overdue books")
        
        with col3:
            # Popular books
            c.execute('''
                SELECT b.title, COUNT(*) as issue_count
                FROM transactions t
                JOIN books b ON t.book_id = b.book_id
                GROUP BY b.book_id
                ORDER BY issue_count DESC
                LIMIT 5
            ''')
            popular_books = c.fetchall()
            
            st.markdown("#### Popular Books")
            for title, issues in popular_books:
                st.markdown(f"""
                    <div style='background-color: #1a1a1a; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem;'>
                        <div style='color: #ffffff;'>{title}</div>
                        <div style='color: #ff0000; font-size: 0.9rem;'>
                            {issues} issues
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    finally:
        conn.close()

def main():
    # Initialize database
    init_db()
    
    # Initialize sample data if database is empty
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM books')
    if c.fetchone()[0] == 0:
        initialize_sample_data()
    conn.close()
    
    render_header()
    
    # Add RFID Scanner to sidebar
    with st.sidebar:
        render_rfid_scanner()
        st.markdown("---")
    
    render_metrics()
    render_search()
    render_stats()
    render_forms()
    render_tables()
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div class='footer' style='text-align: center;'>
            <p style='color: #ffffff; font-size: 0.9rem; opacity: 0.8;'>© 2024 Library Management System | Made with ❤️</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

