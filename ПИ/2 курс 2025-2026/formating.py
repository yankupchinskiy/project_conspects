import os

directory = '4 Семестр/ТВиМС'

for filename in os.listdir(directory):
    if filename.endswith('.md'):
        filepath = os.path.join(directory, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Выполняем замены по правилам:
        # /(  ->  $
        # /)  ->  $
        # /[  ->  $$
        # /]  ->  $$
        new_content = content.replace('\\( ', '$')
        new_content = new_content.replace(' \\)', '$')
        new_content = new_content.replace('\\(', '$')
        new_content = new_content.replace('\\)', '$')
        new_content = new_content.replace('\\[', '$$')
        new_content = new_content.replace('\\]', '$$')

        # Записываем обратно в тот же файл
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f'Обработан: {filename}')