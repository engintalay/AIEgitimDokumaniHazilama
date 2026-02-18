import yaml
from core.vector_db import VectorDB
from tabulate import tabulate

def check_db():
    try:
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        cfg = config.get('rag', {})
        db = VectorDB(
            db_path=cfg.get('db_path', './data/vector_db'),
            collection_name=cfg.get('collection_name', 'training_docs')
        )
        
        count = db.get_collection_count()
        
        # Get a sample to see metadata structure
        sample = db.collection.get(limit=10)
        
        print("\n" + "="*40)
        print("📊 VEKTÖR VERİ TABANI DURUMU")
        print("="*40)
        print(f"📍 DB Yolu: {cfg.get('db_path')}")
        print(f"📂 Koleksiyon: {cfg.get('collection_name')}")
        print(f"🔢 Toplam Paragraf Sayısı: {count}")
        print("-" * 40)
        
        if count > 0:
            print("\n📈 Son Eklenen / Örnek Kayıtlar:")
            table_data = []
            for i in range(len(sample['ids'])):
                source = sample['metadatas'][i].get('source', 'Bilinmiyor')
                text_snippet = sample['documents'][i][:70].replace('\n', ' ') + "..."
                table_data.append([sample['ids'][i], source, text_snippet])
            
            print(tabulate(table_data, headers=["ID", "Kaynak Dosya", "Metin Önizleme"], tablefmt="grid"))
        else:
            print("\n⚠️ Veri tabanı şu an boş.")
            
        print("="*40 + "\n")

    except Exception as e:
        print(f"❌ Hata oluştu: {str(e)}")

if __name__ == "__main__":
    check_db()
