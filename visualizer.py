import os
import sys
import requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Исправление кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv(override=True)

client = OpenAI()

def generate_house_render(prompt, output_folder, filename):
    """Генерирует изображение дома через DALL-E 3"""
    
    print(f"\n🎨 Генерирую: {filename}...")
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",  # Широкоформатный рендер
            quality="hd",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # Скачиваем изображение
        img_response = requests.get(image_url)
        
        os.makedirs(output_folder, exist_ok=True)
        filepath = f"{output_folder}/{filename}.png"
        
        with open(filepath, 'wb') as f:
            f.write(img_response.content)
        
        print(f"✅ Сохранено: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def main():
    print("=" * 60)
    print("🏠 ВИЗУАЛИЗАТОР ДОМА В ЮРМАЛЕ (DALL-E 3)")
    print("=" * 60)
    
    # Папка для рендеров
    output_folder = "./projects/Modern_private_house_design_in/renders"
    
    # Базовое описание дома
    base_description = """
    Modern minimalist private house in Jurmala Bulduri, Latvia.
    250 sqm living space on 1000 sqm pine forest plot.
    Contemporary Scandinavian architecture.
    Large floor-to-ceiling windows.
    Natural materials: wood, stone, glass.
    Flat roof with wooden terrace.
    Integration with pine trees and Baltic nature.
    Warm evening lighting.
    Professional architectural photography style.
    """
    
    renders = [
        {
            "name": "exterior_front",
            "prompt": f"Photorealistic exterior front view of a {base_description} Wide angle shot showing entrance and driveway. Golden hour lighting. 8K architectural visualization."
        },
        {
            "name": "exterior_garden",
            "prompt": f"Photorealistic garden view of a {base_description} View from the backyard showing large terrace, outdoor living space, pine trees around. Summer day. 8K architectural render."
        },
        {
            "name": "interior_living",
            "prompt": f"Photorealistic interior of modern living room in {base_description} Open plan living area with double-height ceiling, minimalist furniture, large windows with forest view. Warm natural light. 8K interior design visualization."
        },
        {
            "name": "aerial_view",
            "prompt": f"Aerial drone view of a {base_description} Bird's eye perspective showing the house layout, garden, pine forest surroundings. Summer. 8K architectural drone photography."
        }
    ]
    
    print(f"\n📁 Рендеры будут сохранены в: {output_folder}")
    print(f"🖼️  Количество изображений: {len(renders)}")
    print("\n" + "-" * 60)
    
    generated = []
    for render in renders:
        result = generate_house_render(
            render["prompt"], 
            output_folder, 
            render["name"]
        )
        if result:
            generated.append(result)
    
    print("\n" + "=" * 60)
    print(f"🎉 ГОТОВО! Создано {len(generated)} из {len(renders)} рендеров")
    print("=" * 60)
    print("\nФайлы:")
    for path in generated:
        print(f"  📷 {path}")

if __name__ == "__main__":
    main()


