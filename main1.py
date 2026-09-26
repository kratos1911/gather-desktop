import sys
import os
from PyQt6 import sip
import json
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLineEdit, QPushButton, QListWidget, 
                           QListWidgetItem, QLabel, QTextEdit, QFileDialog,
                           QStackedWidget, QSplitter, QMessageBox, QProgressDialog,
                           QFrame, QToolButton)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon
# Add these imports at the top of your file
from PyQt6.QtCore import QUrl

from llama_index.llms.ollama import Ollama
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex
from llama_index.core.embeddings import resolve_embed_model
import os
import fitz  # PyMuPDF for PDFs
import docx  # python-docx for DOCX files
from pptx import Presentation  # python-pptx for PPTX files
from llama_index.core import Settings
from llama_index.core.schema import Document
import shutil
import chromadb
from typing import List, Optional
from docx import Document as DocxDocument
import PyPDF2

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    print("QtWebEngine not available - PDF, DOCX and PPTX viewing will be limited to text")

# Import document parsing libraries - with proper error handling
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pptx
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False




llm = Ollama(model="mistral", request_timeout=300.0)
embed_model = resolve_embed_model("local:BAAI/bge-m3")
Settings.llm = Ollama(model="mistral", request_timeout=300.0)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="file_embeddings",embedding_function=None)


global vector_index_global

# # Worker thread for file processing
# class FileProcessingThread(QThread):
#     finished = pyqtSignal(VectorStoreIndex, str)
#     error = pyqtSignal(str)

#     def __init__(self, file_path, temp_path):
#         super().__init__()
#         self.file_path = file_path
#         self.temp_path = temp_path

#     def run(self):
#         try:
#             # content = self.extract_content(self.temp_path)
#             documents = process_documents()
#             vector_index = create_index(documents)
#             vector_index_global = vector_index
#             # create_document_embedding(vector_index=vector_index)
#             self.finished.emit(vector_index, self.temp_path)

#         except Exception as e:
#             self.error.emit(str(e))

#     def extract_content(self, file_path):
#         """Extract content from various file types"""
#         _, ext = os.path.splitext(file_path)
#         ext = ext.lower()

#         # Process different file types
#         if ext in ['.txt', '.md', '.py', '.java', '.c', '.cpp', '.html', '.css', '.js']:
#             return self.read_text_file(file_path)
#         elif ext == '.pdf' and PDF_AVAILABLE:
#             return self.extract_pdf_content(file_path)
#         elif ext == '.docx' and DOCX_AVAILABLE:
#             return self.extract_docx_content(file_path)
#         elif ext in ['.pptx', '.ppt'] and PPTX_AVAILABLE:
#             return self.extract_pptx_content(file_path)
#         else:
#             # For unsupported formats, try to read as text
#             try:
#                 return self.read_text_file(file_path)
#             except:
#                 return f"[This file type ({ext}) is not fully supported. No content could be extracted.]"

# Worker thread for file processing
class FileProcessingThread(QThread):
    finished = pyqtSignal(VectorStoreIndex, str)
    error = pyqtSignal(str)

    def __init__(self, file_path, temp_file_path):
        super().__init__()
        self.file_path = file_path
        self.temp_file_path = temp_file_path

    def run(self):
        try:
            # Step 1: Process documents from temp path
            # documents = process_documents(temp_dir=self.temp_path, final_dir=self.file_path)
            """
            # Step 2: Create vector index
            vector_index = create_index(documents)

            # Step 3: Store embeddings into ChromaDB
            create_document_embedding(vector_index=vector_index)

            # Step 4: Emit finished signal with vector index and path
            self.finished.emit(vector_index, self.temp_path)"""
            filename = os.path.basename(self.file_path)
            ext = os.path.splitext(filename)[1].lower()
            text = ""

            if ext == ".pdf" and PDF_AVAILABLE:
                with fitz.open(self.file_path) as pdf_doc:
                    text += "\n".join([page.get_text() for page in pdf_doc])
            elif ext == ".txt":
                with open(self.file_path, "r", encoding="utf-8") as f:
                    text += f.read()
            elif ext in [".doc", ".docx"] and DOCX_AVAILABLE:
                doc = docx.Document(self.file_path)
                text += "\n".join([para.text for para in doc.paragraphs])
            elif ext == ".pptx" and PPTX_AVAILABLE:
                ppt = Presentation(self.file_path)
                text += "\n".join([
                    shape.text for slide in ppt.slides for shape in slide.shapes if hasattr(shape, "text") and shape.text
                ])
            else:
                print("Legacy operation: private details omitted.")
                return None

            document = Document(text=text, metadata={"filename": filename})
            dest_path = os.path.join("./data", os.path.basename(self.file_path))
            shutil.move(self.file_path, dest_path)
            print("Legacy operation: private details omitted.")

            vector_index = VectorStoreIndex.from_documents([document], embed_model=embed_model)
            node = list(vector_index.docstore.docs.values())[0]
            doc_id = node.id_
            metadata = node.metadata or {}
            if node.embedding is None:
                node.embedding = embed_model.get_text_embedding(node.text)
            embedding = node.embedding

            collection.add(
                documents=[node.text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[doc_id]
            )

            self.finished.emit(vector_index, self.temp_file_path)


        except Exception as e:
            self.error.emit(str(e))

class DocumentViewer(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def load_document(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.setPlainText(content)
        except Exception as e:
            self.setPlainText(f"Failed to load document: {e}")
        
        # Create text viewer for fallback
        self.text_viewer = QTextEdit()
        self.text_viewer.setReadOnly(True)
        self.text_viewer.setFont(QFont("Segoe UI", 12))
        self.addWidget(self.text_viewer)
        
        # Create web viewer if QtWebEngine is available
        if WEBENGINE_AVAILABLE:
            self.web_viewer = QWebEngineView()
            # Enable PDF viewing
            settings = self.web_viewer.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
            self.addWidget(self.web_viewer)
    
    def display_document(self, file_path, content):
        """Display a document based on its file type"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Handle different file types
        if ext == '.pdf' and WEBENGINE_AVAILABLE:
            # For PDF files, use QtWebEngine's built-in PDF viewer
            file_url = QUrl.fromLocalFile(file_path)
            self.web_viewer.load(file_url)
            self.setCurrentWidget(self.web_viewer)
            return True
        else:
            # Fallback to text display
            self.text_viewer.setPlainText(content)
            self.setCurrentWidget(self.text_viewer)
            return False

class DocumentManager:
    def __init__(self, folder_path: str = "data"):
        self.folder_path = folder_path
        os.makedirs(self.folder_path, exist_ok=True)  # Ensure folder exists

    def get_all_documents(self) -> List[str]:
        return [
        {
            'name': f,
            'id': str(hash(f)),  # Unique ID
            'path': os.path.join(self.folder_path, f)
        }
        for f in os.listdir(self.folder_path)
        if os.path.isfile(os.path.join(self.folder_path, f))
    ]

    def get_document_path(self, filename: str) -> str:
        return os.path.join(self.folder_path, filename)
    
    def get_document_by_id(self, doc_id):
        for file_name in os.listdir(self.folder_path):
            full_path = os.path.join(self.folder_path, file_name)
            if os.path.isfile(full_path) and str(hash(file_name)) == str(doc_id):
                return {
                    'name': file_name,
                    'id': doc_id,
                    'path': full_path
                }
        return None
    def read_document(self, filename: str) -> Optional[str]:
        file_path = self.get_document_path(filename)
        _, ext = os.path.splitext(filename.lower())

        try:
            if ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as file:
                    return file.read()
            elif ext == ".pdf":
                return self._read_pdf(file_path)
            elif ext == ".docx":
                return self._read_docx(file_path)
            else:
                print("Legacy operation: private details omitted.")
                return None
        except Exception as e:
            print("Legacy operation: private details omitted.")
            return None

    def save_document(self, filename: str, content: str) -> bool:
        file_path = self.get_document_path(filename)
        _, ext = os.path.splitext(filename.lower())

        if ext != ".txt":
            print("Only .txt files are supported for saving.")
            return False

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)
            return True
        except Exception as e:
            print("Legacy operation: private details omitted.")
            return False

    def delete_document(self, filename: str) -> bool:
        try:
            os.remove(self.get_document_path(filename))
            return True
        except Exception as e:
            print("Legacy operation: private details omitted.")
            return False

    def _read_pdf(self, path: str) -> str:
        text = ""
        try:
            with open(path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            print("Legacy operation: private details omitted.")
        return text

    def _read_docx(self, path: str) -> str:
        text = ""
        try:
            doc = DocxDocument(path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print("Legacy operation: private details omitted.")
        return text

# Main application class

class DocumentChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize application data
        self.documents = {}
        self.current_document = None
        self.doc_manager = DocumentManager(folder_path = "data")
        self.temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Load existing documents if available
        #self.load_documents()
        
        # Set up the UI
        self.init_ui()

        # collection = init_db()
        
        # Display dependency info
        self.show_dependency_info()
    
            
    def show_dependency_info(self):
        """Show information about missing dependencies"""
        missing_libs = []
        
        if not DOCX_AVAILABLE:
            missing_libs.append("python-docx (for Word documents)")
        if not PPTX_AVAILABLE:
            missing_libs.append("python-pptx (for PowerPoint presentations)")
        if not PDF_AVAILABLE:
            missing_libs.append("PyMuPDF (for PDF files)")
            
        if missing_libs:
            message = ("Some file formats won't be fully supported. To enable all features, install:\n\n" + 
                      "\n".join([f"- {lib}" for lib in missing_libs]) +
                      "\n\nYou can install them using:\npip install python-docx python-pptx pymupdf chardet")
            
            QMessageBox.information(self, "Optional Dependencies", message)
        
    def init_ui(self):
        # Main window setup
        self.setWindowTitle("Intelligent Information Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget(self)
        layout = QVBoxLayout() 

        # Set the application style and colors
        self.setup_colors()

        self.document_list_widget = QListWidget()
        self.document_list_widget.itemClicked.connect(self.document_selected)

        # Add it to the layout
        layout.addWidget(self.document_list_widget)

        # Set layout on central widget
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Now it's safe to call this
        self.update_document_list()
        
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)  # Changed to horizontal layout
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for a cleaner look
        
        # Create sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(300)
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        
        # App title in sidebar
        title_label = QLabel("Intelligent\nInformation\nManager")
        title_font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addSpacing(20)
        
        # Add document button
        add_button = QPushButton("+ Add New Document")
        add_button.setFont(QFont("Segoe UI", 12))
        add_button.setMinimumHeight(45)
        add_button.clicked.connect(self.add_document)
        sidebar_layout.addWidget(add_button)
        sidebar_layout.addSpacing(15)
        
        # Documents label
        docs_label = QLabel("Your Documents")
        docs_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        sidebar_layout.addWidget(docs_label)
        
        # Document list
        self.document_list = QListWidget()
        self.document_list.setFont(QFont("Segoe UI", 12))
        # In the init_ui method, update the document_list stylesheet:
        self.document_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                color: black;
            }
            QListWidget::item { 
                padding: 10px;
                margin-bottom: 5px;
                border-radius: 6px;
                background-color: #FFFFFF;
                color: black;
            }
            QListWidget::item:selected { 
                background-color: #f0f7ff;
                color: #0060df;
            }
        """)    
        sidebar_layout.addWidget(self.document_list)
        
        # Create main content area with stacked widget
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()
        
        # Create search screen
        search_screen = QWidget()
        search_layout = QVBoxLayout(search_screen)
        search_layout.setSpacing(20)
        search_layout.setContentsMargins(30, 30, 30, 30)
        
        # Center section for search
        center_section = QWidget()
        center_layout = QVBoxLayout(center_section)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setContentsMargins(50, 50, 50, 50)
        
        # Search bar container
        search_container = QWidget()
        search_container_layout = QVBoxLayout(search_container)
        search_container_layout.setContentsMargins(50, 10, 50, 10)
        
        # Search instruction
        search_label = QLabel("Search your documents")
        search_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        search_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        search_container_layout.addWidget(search_label)
        
        # Search bar
        self.search_bar = QLineEdit()
        search_font = QFont("Segoe UI", 14)
        self.search_bar.setFont(search_font)
        self.search_bar.setPlaceholderText("Type to search...")
        self.search_bar.setMinimumHeight(50)
        # self.search_bar.textChanged.connect(self.filter_documents)
        search_container_layout.addWidget(self.search_bar)
        self.search_button = QPushButton("Search for this Document")
        self.search_button.setFont(QFont("Segoe UI", 12))
        self.search_button.setMinimumHeight(45)
        self.search_button.clicked.connect(self.filter_documents)
        search_container_layout.addWidget(self.search_button)
        
        center_layout.addWidget(search_container)
        
        # Selected document actions
        self.doc_actions = QWidget()
        doc_actions_layout = QHBoxLayout(self.doc_actions)
        doc_actions_layout.setContentsMargins(50, 10, 50, 10)
        
        self.selected_doc_label = QLabel("No document selected")
        self.selected_doc_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.selected_doc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        doc_actions_layout.addWidget(self.selected_doc_label)
        
        center_layout.addWidget(self.doc_actions)
        
        # Action buttons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(50, 10, 50, 10)
        buttons_layout.setSpacing(20)
        
        # self.open_button = QPushButton("Open Document")
        # self.open_button.setFont(QFont("Segoe UI", 12))
        # self.open_button.setMinimumHeight(45)
        # self.open_button.clicked.connect(self.open_selected_document)
        # self.open_button.setEnabled(False)
        # buttons_layout.addWidget(self.open_button)
        
        # self.chat_button = QPushButton("Chat with Document")
        # self.chat_button.setFont(QFont("Segoe UI", 12))
        # self.chat_button.setMinimumHeight(45)
        # self.chat_button.clicked.connect(self.chat_with_selected_document)
        # self.chat_button.setEnabled(False)
        # buttons_layout.addWidget(self.chat_button)
        
        # center_layout.addWidget(buttons_container)
        
        search_layout.addWidget(center_section)
        search_layout.addStretch(1)
        
        # Create chat screen
        self.chat_screen = QWidget()
        chat_layout = QVBoxLayout(self.chat_screen)
        chat_layout.setContentsMargins(0, 0, 0, 0)  # Clean margins
        
        # Chat header
        chat_header = QWidget()
        chat_header.setFixedHeight(70)
        chat_header.setObjectName("chatHeader")
        chat_header_layout = QHBoxLayout(chat_header)
        chat_header_layout.setContentsMargins(20, 0, 20, 0)
        
        back_button = QPushButton("← Back")
        back_button.setFont(QFont("Segoe UI", 12))
        back_button.setFixedWidth(100)
        back_button.clicked.connect(self.go_back_to_search)
        chat_header_layout.addWidget(back_button)
        
        self.chat_title = QLabel("Document Chat")
        self.chat_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        chat_header_layout.addWidget(self.chat_title)
        
        chat_header_layout.addStretch(1)
        
        chat_layout.addWidget(chat_header)
        
        # Chat splitter
        chat_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Document content widget
        document_widget = QWidget()
        document_layout = QVBoxLayout(document_widget)
        document_layout.setContentsMargins(20, 20, 20, 20)
        
        document_header = QLabel("Document Content")
        document_header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        document_layout.addWidget(document_header)
        
        # self.document_content = QTextEdit()
        # self.document_content.setFont(QFont("Segoe UI", 12))
        # self.document_content.setReadOnly(True)
        self.document_content = DocumentViewer()
        # document_layout.addWidget(self.document_content)
        document_layout.addWidget(self.document_content)
        
        # Conversation widget
        conversation_widget = QWidget()
        conversation_layout = QVBoxLayout(conversation_widget)
        conversation_layout.setContentsMargins(20, 20, 20, 20)
        
        conversation_header = QLabel("Conversation")
        conversation_header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        conversation_layout.addWidget(conversation_header)
        
        self.conversation_history = QTextEdit()
        self.conversation_history.setFont(QFont("Segoe UI", 12))
        self.conversation_history.setReadOnly(True)
        conversation_layout.addWidget(self.conversation_history)
        
        chat_input_container = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setFont(QFont("Segoe UI", 12))
        self.chat_input.setPlaceholderText("Type your message...")
        self.chat_input.setMinimumHeight(40)
        self.chat_input.returnPressed.connect(self.send_message)
        chat_input_container.addWidget(self.chat_input)
        
        send_button = QPushButton("Send")
        send_button.setFont(QFont("Segoe UI", 12))
        send_button.setFixedWidth(80)
        send_button.setMinimumHeight(40)
        send_button.clicked.connect(self.send_message)
        chat_input_container.addWidget(send_button)
        
        conversation_layout.addLayout(chat_input_container)
        
        # Add widgets to splitter
        chat_splitter.addWidget(document_widget)
        chat_splitter.addWidget(conversation_widget)
        chat_splitter.setSizes([500, 500])
        
        chat_layout.addWidget(chat_splitter)
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(search_screen)
        self.stacked_widget.addWidget(self.chat_screen)
        
        # Add stacked widget to content layout
        content_layout.addWidget(self.stacked_widget)
        
        # Add sidebar and content area to main layout
        main_layout.addWidget(sidebar)
        
        # Add a vertical separator between sidebar and content
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #D0D0D0;")
        main_layout.addWidget(separator)
        
        main_layout.addWidget(content_area)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Populate document list
        self.update_document_list()
        
        # Connect document list selection
        self.document_list.itemClicked.connect(self.document_selected)
    
    def setup_colors(self):
        """Set up color palette for the application"""
        # Create a palette with light colors
        palette = QPalette()
        
        # Set window background color
        palette.setColor(QPalette.ColorRole.Window, QColor("#F5F9FC"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#333333"))
        
        # Set colors for widgets
        palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F0F7FF"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#333333"))
        
        # Set colors for buttons
        palette.setColor(QPalette.ColorRole.Button, QColor("#0060DF"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#FFFFFF"))
        
        # Set highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#0060DF"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        
        # Apply palette
        QApplication.setPalette(palette)
        
        # Set stylesheet for custom elements
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F9FC;
            }
            #sidebar {
                background-color: #F0F7FF;
                color: #000;
                border-right: 1px solid #D0D0D0;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #D0D0D0;
                border-radius: 6px;
                background-color: white;
                color: #333333;
            }
            QPushButton {
                background-color: #0060DF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052CC;
            }
            QPushButton:pressed {
                background-color: #0046B8;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
            QListWidget {
                border: none;
                border-radius: 6px;
                background-color: transparent;
                padding: 5px;
                color: #333333;
            }
            QTextEdit {
                border: 1px solid #D0D0D0;
                border-radius: 6px;
                background-color: white;
                padding: 10px;
                color: #333333;
                selection-background-color: #E1EFFF;
                selection-color: #333333;
            }
            #chatHeader {
                background-color: #FFFFFF;
                border-bottom: 1px solid #D0D0D0;
            }
            QToolButton {
                border: none;
                background-color: transparent;
            }
        """)
        self.setStyleSheet(self.styleSheet() + """
            #sidebar QLabel {
                color: black;
            }
            QListWidget {
                color: black !important;
            }
            QListWidget::item {
                color: black !important;
            }
            QToolButton {
                color: black;
            }
        """)
    
    def create_document_item(self, doc_id, doc_info):
        """Create a customized document list item with delete button"""
        # Create widget for the item
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(10, 5, 10, 5)
        
        # Document title
        doc_title = QLabel(doc_info['title'])
        doc_title.setFont(QFont("Segoe UI", 11))
        doc_title.setStyleSheet("color: black;")  # Force black text
        doc_title.setWordWrap(True)
        item_layout.addWidget(doc_title, 1)  # Stretch factor 1
        
        # Delete button
        delete_btn = QToolButton()
        delete_btn.setText("×")  # Using a simple X character as delete icon
        delete_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        delete_btn.setToolTip("Delete document")
        delete_btn.setFixedSize(25, 25)
        delete_btn.setProperty("doc_id", doc_id)
        delete_btn.setStyleSheet("color: black;") 
        delete_btn.clicked.connect(lambda: self.delete_document(doc_id))
        item_layout.addWidget(delete_btn)
        
        # Create list item
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, doc_id)
        item.setSizeHint(item_widget.sizeHint())
        
        return item, item_widget
    
    def update_document_list(self):
        try:

            # if hasattr(self, 'document_list_widget') and self.document_list_widget:
            #     if not sip.isdeleted(self.document_list_widget):
            #         self.document_list_widget.clear()
            for filename in os.listdir("/data"):
                item = QListWidgetItem(filename)
                item.setData(Qt.ItemDataRole.UserRole, filename)
                self.document_list_widget.addItem(item)
        except Exception as e:
            print("Legacy operation: private details omitted.")


    def filter_documents(self):
        """Filter documents based on search query"""
        try:
            top_k = 1
            query = self.search_bar.text().lower()
            query_embedding = embed_model.get_text_embedding(query)
            results = collection.query(query_embeddings=[query_embedding],n_results=top_k)
            if results and results.get("metadatas") and len(results["metadatas"][0]) > 0:
                matched_files = results["metadatas"][0]
                best_match = matched_files[0]

                print("Legacy operation: private details omitted.")

                file_name = best_match.get("filename", "Unknown File")
                doc_id = best_match.get("doc_id")

                # 🔁 Load full document text from saved JSON
                doc_path = os.path.join("data", f"{file_name}")
                os.system(f'start "" "{doc_path}"')  # Open the document in the default viewer
                # if os.path.exists(doc_path):
                #     with open(doc_path, "r", encoding="utf-8") as f:
                #         doc_data = json.load(f)
                #         document_text = doc_data.get("text", "")
                #         print(doc_path)
                #         # return file_name, document_text
                # else:
                #     print("⚠️ Document text file not found!")
        except Exception as e:
            print("Legacy operation: private details omitted.")

    
    def add_document(self):
        """Add a new document"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select Document", "", 
            "Documents (*.txt *.pdf *.docx *.pptx *.ppt);;Text Files (*.txt);;PDF Files (*.pdf);;Word Files (*.docx);;PowerPoint Files (*.pptx);;All Files (*)"
        )
        
        if file_path:
            
            file_name = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_filename = f"{timestamp}_{file_name}"
            temp_file_path = os.path.join(self.temp_dir, unique_filename)
            
            try:
                shutil.copy2(file_path, temp_file_path)
            
                progress = QProgressDialog("Processing document...", "Cancel", 0, 0, self)
                progress.setWindowTitle("Loading Document")
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.show()
            
                self.file_thread = FileProcessingThread(file_path, temp_file_path)
                self.file_thread.finished.connect(lambda content, path: self.document_processed(content, path, progress))
                print("Legacy operation: private details omitted.")
                self.file_thread.error.connect(lambda error: self.document_processing_error(error, progress))
                self.file_thread.start()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error copying file: {str(e)}")
    
    def document_processed(self, vector_index, file_path, progress_dialog):
        """Called when document processing is finished"""
        progress_dialog.close()

        # doc_id = f"doc_{len(self.documents) + 1}"
        # doc_title = os.path.basename(file_path).split('_', 1)[1]  # Remove timestamp prefix

        # self.documents[doc_id] = {
        #     'title': doc_title,
        #     'path': file_path,
        #     'created_at': datetime.now().isoformat(),
        #     'conversations': []  # Optional: if you want to chat about the doc later
        # }

        # self.save_documents()
        # self.update_document_list()
        # QMessageBox.information(self, "Success", f"Document '{doc_title}' added and indexed successfully.")

        if not hasattr(self, 'document_list_widget') or self.document_list_widget is None:
            print("Widget already deleted, skipping update.")
            return

        try:
            # your processing logic...
            doc_title = os.path.basename(file_path)
            self.update_document_list()

            if self.isVisible():
                QMessageBox.information(self, "Success", f"Document '{doc_title}' added and indexed successfully.")
        except RuntimeError as e:
            print("Legacy operation: private details omitted.")
        
    def document_processing_error(self, error, progress_dialog):
        """Called when document processing encounters an error"""
        progress_dialog.close()
        print("Legacy operation: private details omitted.")
        QMessageBox.critical(self, "Error", f"Error processing document: {error}")
        
    def delete_document(self, doc_id):
        """Delete a document from the list and temp directory"""
        if doc_id in self.documents:
            # Ask for confirmation
            confirm = QMessageBox.question(
                self, "Confirm Deletion", 
                f"Are you sure you want to delete '{self.documents[doc_id]['title']}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                # Delete the file from temp directory
                try:
                    file_path = self.documents[doc_id]['path']
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print("Legacy operation: private details omitted.")
                
                # Remove from documents dictionary
                del self.documents[doc_id]
                
                # Save documents
                self.save_documents()
                
                # Update document list
                self.update_document_list()
                
                # Reset selected document if it was the deleted one
                if self.current_document == doc_id:
                    self.current_document = None
                    # self.selected_doc_label.setText("No document selected")
                    self.open_button.setEnabled(False)
                    self.chat_button.setEnabled(False)
    
    def document_selected(self, item):
        
        doc_id = item.data(Qt.ItemDataRole.UserRole)
        doc_name = item.text()
        self.selected_doc_id = doc_id  # Store it as an instance variable
        self.selected_doc_label.setText(f"Selected: {doc_name}")
        self.open_button.setEnabled(True)
        self.chat_button.setEnabled(True)

    
    def open_selected_document(self):
        # """Open the selected document content"""
        # if not self.current_document:
        #     return
            
        # doc_info = self.documents[self.current_document]
        # success = self.document_content.display_document(doc_info['path'], doc_info['content'])
        
        # if not success and WEBENGINE_AVAILABLE:
        #     QMessageBox.information(self, "Notice", "This file type cannot be viewed directly. Showing extracted text instead.")
        
        # self.chat_title.setText(doc_info['title'])
        # self.stacked_widget.setCurrentIndex(1)
       
        if not hasattr(self, 'selected_doc_id') or not self.selected_doc_id:
            return
        
        document = {'name': self.selected_doc_id}
        if document:
            self.document_content.load_document(document['path'])  # Your display logic
            self.stacked_widget.setCurrentWidget(self.chat_screen)




    def chat_with_selected_document(self):
        """Open chat interface for the selected document"""
        if not self.current_document:
            return
            
        doc_info = self.documents[self.current_document]
        self.document_content.display_document(doc_info['path'], doc_info['content'])
        self.chat_title.setText(doc_info['title'])
        
        # Load conversation history
        self.refresh_conversation_history()
        
        # Switch to chat view
        self.stacked_widget.setCurrentIndex(1)    
    def open_document(self, item):
        """Open document in chat view (kept for compatibility)"""
        doc_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_document = doc_id
        self.chat_with_selected_document()
    
    def refresh_conversation_history(self):
        """Refresh the conversation history display"""
        if not self.current_document:
            return
        
        doc_info = self.documents[self.current_document]
        conversations = doc_info.get('conversations', [])
        
        # Clear current display
        self.conversation_history.clear()
        
        # Format and display conversations with better styling
        formatted_history = """
        <style>
            .message-container { margin-bottom: 16px; }
            .user-message { 
                background-color: #E1EFFF; 
                color: #0060DF; 
                padding: 10px 15px; 
                border-radius: 18px 18px 4px 18px;
                display: inline-block;
                max-width: 80%;
                margin-left: 40px;
                position: relative;
            }
            .doc-message { 
                background-color: #F0F0F0; 
                color: #333333; 
                padding: 10px 15px; 
                border-radius: 18px 18px 18px 4px;
                display: inline-block;
                max-width: 80%;
                margin-right: 40px;
                position: relative;
            }
            .sender { 
                font-weight: bold; 
                margin-bottom: 5px;
                font-size: 12px;
                margin-left: 15px;
}
        </style>
        """
        
        for msg in conversations:
            if msg['sender'] == 'user':
                formatted_history += f"""
                <div class="message-container" align="right">
                    <div class="sender" align="right">You</div>
                    <div class="user-message">{msg['text']}</div>
                </div>
                """
            else:
                formatted_history += f"""
                <div class="message-container" align="left">
                    <div class="sender" align="left">Document</div>
                    <div class="doc-message">{msg['text']}</div>
                </div>
                """
        
        self.conversation_history.setHtml(formatted_history)
        
        # Scroll to bottom
        scrollbar = self.conversation_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def send_message(self):
        """Send a message in the conversation"""
        if not self.current_document:
            return
        
        message = self.chat_input.text().strip()
        if not message:
            return
        
        # Add user message to conversation
        doc_info = self.documents[self.current_document]
        if 'conversations' not in doc_info:
            doc_info['conversations'] = []
        
        doc_info['conversations'].append({
            'sender': 'user',
            'text': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Generate a response based on document content
        doc_content = doc_info['content'].lower()
        user_query = message.lower()
        
        # Simple response logic - check if keywords from the query appear in the document
        keywords = user_query.split()
        relevant_sentences = []
        
        # Split document into sentences and find relevant ones
        sentences = doc_content.replace('\n', ' ').split('. ')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            for keyword in keywords:
                if keyword in sentence and sentence not in relevant_sentences and len(sentence) > 10:
                    relevant_sentences.append(sentence)
                    break
        
        # Generate response
        if relevant_sentences:
            response = f"I found this in the document: \"{'. '.join(relevant_sentences[:2])}.\""
        else:
            response = "I couldn't find specific information about that in the document. Can you try rephrasing your question?"
        
        # Add document response to conversation
        doc_info['conversations'].append({
            'sender': 'document',
            'text': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Save changes
        self.save_documents()
        
        # Update conversation display
        self.refresh_conversation_history()
        
        # Clear input field
        self.chat_input.clear()
    
    def go_back_to_search(self):
        """Return to search screen"""
        self.stacked_widget.setCurrentIndex(0)
    
    def save_documents(self):
        """Save documents to a JSON file"""
        pass

    def load_documents(self):
        """Load document files from ./data folder"""
        self.documents = {}
        data_dir = "./data"
        for file in os.listdir(data_dir):
            path = os.path.join(data_dir, file)
            if os.path.isfile(path):
                doc_id = os.path.splitext(file)[0]
                self.documents[doc_id] = {
                    "filename": file,
                    "path": path
                }

    def document_loaded(self, doc_id, doc_info, content, progress_dialog):
        """Called when a document is successfully loaded"""
        # Store document with content
        self.documents[doc_id] = doc_info
        self.documents[doc_id]['content'] = content
        
        # Close progress dialog after last document
        progress_dialog.close()
    
    def document_loading_error(self, doc_id, error, progress_dialog):
        """Called when there's an error loading a document"""
        print("Legacy operation: private details omitted.")
        progress_dialog.close()









# Main function to run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DocumentChatApp()
    window.show()
    sys.exit(app.exec())