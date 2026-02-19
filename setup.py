from setuptools import setup, find_packages

setup(
    name="ai-egitim-dokumani-hazirlama",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "Flask>=3.0.0",
        "Flask-SQLAlchemy>=3.1.0",
        "Flask-Login>=0.6.0",
        "Authlib>=1.3.0",
        "PyYAML>=6.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "chromadb>=0.4.0",
        "PyMuPDF>=1.23.0",
        "python-docx>=1.1.0",
        "tqdm>=4.66.0",
        "pdfplumber>=0.10.0",
        "pdfminer.six>=20221105",
        "lxml>=5.1.0",
        "openai>=1.10.0",
    ],
    author="Engin Talay",
    description="AI tabanlı eğitim dokümanı hazırlama ve asistan uygulaması",
    keywords="AI, Education, RAG, NLP, Document Processing",
    url="https://github.com/engintalay/AIEgitimDokumaniHazilama",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
