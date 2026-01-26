# **Умные указатели и std::unique_ptr в C++**

## **Что такое умный указатель?**

**Умный указатель (smart pointer)** — это объект-обертка над сырым (raw) указателем, который автоматически управляет временем жизни динамически выделенной памяти. Это одна из ключевых идиом **RAII (Resource Acquisition Is Initialization)** в C++.

### **Проблема сырых указателей**
```cpp
// Проблемный код с сырыми указателями
void problematic_function() {
    int* raw_ptr = new int[100];  // Выделили память
    
    if (some_condition()) {
        throw std::runtime_error("Ошибка!");  // Память НЕ освобождается!
        // Утечка памяти: delete[] не вызывается
    }
    
    // Ещё хуже:
    int* ptr2 = raw_ptr;
    delete[] raw_ptr;
    // ptr2 теперь висячий указатель (dangling pointer)
    
    delete[] raw_ptr;  // Двойное удаление - неопределенное поведение!
}
```

### **Решение через умные указатели**
```cpp
#include <memory>

void safe_function() {
    std::unique_ptr<int[]> smart_ptr(new int[100]);  // Выделили память
    
    if (some_condition()) {
        throw std::runtime_error("Ошибка!");  // Память ВСЕГДА освобождается!
        // Деструктор unique_ptr вызовет delete[] автоматически
    }
    
    // Никаких утечек, двойных удалений или висячих указателей
    // Память освободится при выходе из области видимости
}
```

## **Типы умных указателей в C++**

1. **`std::unique_ptr`** — эксклюзивное владение (C++11)
2. **`std::shared_ptr`** — совместное владение с подсчётом ссылок (C++11)
3. **`std::weak_ptr`** — "слабая" ссылка без владения (C++11)
4. **`std::auto_ptr`** — устаревший, не используйте (до C++17)

## **Особенности std::unique_ptr**

### **1. Эксклюзивное владение (Unique Ownership)**
Каждый объект принадлежит ровно одному `unique_ptr`. Нельзя скопировать, можно только перемещать.

```cpp
#include <memory>
#include <iostream>

class Resource {
public:
    Resource() { std::cout << "Ресурс создан\n"; }
    ~Resource() { std::cout << "Ресурс уничтожен\n"; }
    void use() { std::cout << "Ресурс используется\n"; }
};

int main() {
    // Создание unique_ptr
    std::unique_ptr<Resource> ptr1(new Resource());
    
    // НЕЛЬЗЯ КОПИРОВАТЬ!
    // std::unique_ptr<Resource> ptr2 = ptr1;  // Ошибка компиляции
    
    // МОЖНО ПЕРЕМЕЩАТЬ
    std::unique_ptr<Resource> ptr2 = std::move(ptr1);  // Перемещение
    
    std::cout << "ptr1: " << (ptr1 ? "не пуст" : "пуст") << std::endl;
    std::cout << "ptr2: " << (ptr2 ? "не пуст" : "пуст") << std::endl;
    
    return 0;
}
```
**Вывод:**
```
Ресурс создан
ptr1: пуст
ptr2: не пуст
Ресурс уничтожен
```

### **2. Автоматическое освобождение памяти**
```cpp
void example() {
    {
        std::unique_ptr<int> ptr(new int(42));
        // Работа с указателем
        *ptr = 100;
    }  // Здесь автоматически вызывается delete
    
    // С массивом:
    {
        std::unique_ptr<int[]> arr(new int[10]);
        arr[0] = 1;  // Доступ через оператор []
    }  // Здесь автоматически вызывается delete[]
}
```

### **3. Производительность**
`unique_ptr` имеет **нулевые накладные расходы** по сравнению с сырым указателем:
- Нет счетчика ссылок (в отличие от `shared_ptr`)
- Не требует дополнительной памяти
- Операции инкремента/декремента счетчика не нужны

### **4. Пользовательские удалители (Custom Deleter)**
```cpp
#include <memory>
#include <iostream>
#include <cstdio>

// 1. Функция как удалитель
void file_deleter(FILE* f) {
    if (f) {
        fclose(f);
        std::cout << "Файл закрыт\n";
    }
}

// 2. Функтор как удалитель
struct ArrayDeleter {
    void operator()(int* p) const {
        std::cout << "Удаляю массив\n";
        delete[] p;
    }
};

// 3. Лямбда как удалитель
auto lambda_deleter = [](int* p) {
    std::cout << "Лямбда удаляет объект\n";
    delete p;
};

int main() {
    // Файл с пользовательским удалителем
    std::unique_ptr<FILE, decltype(&file_deleter)> 
        file(fopen("test.txt", "w"), file_deleter);
    
    // Массив с пользовательским удалителем
    std::unique_ptr<int, ArrayDeleter> arr(new int[10]);
    
    // Объект с лямбдой-удалителем
    std::unique_ptr<int, decltype(lambda_deleter)> 
        num(new int(42), lambda_deleter);
    
    return 0;
}
```

### **5. Совместимость с массивами**
```cpp
// Для одиночных объектов
std::unique_ptr<MyClass> obj_ptr(new MyClass());
auto obj_ptr2 = std::make_unique<MyClass>();  // C++14

// Для массивов объектов
std::unique_ptr<int[]> array_ptr(new int[10]);
auto array_ptr2 = std::make_unique<int[]>(10);  // C++14

// Разный синтаксис доступа:
obj_ptr->method();    // Для объектов: ->
array_ptr[0] = 42;    // Для массивов: []
```

### **6. Получение сырого указателя**
```cpp
std::unique_ptr<int> ptr = std::make_unique<int>(42);

// Получить указатель без передачи владения
int* raw = ptr.get();  // Указатель остается у unique_ptr

// Высвободить владение (вернуть сырой указатель и обнулить unique_ptr)
int* released = ptr.release();  // Теперь ВЫ отвечаете за delete released
// ptr теперь пуст

// Сбросить указатель (удалить текущий, принять новый)
ptr.reset(new int(100));  // Старый удаляется, принимается новый
ptr.reset();  // Удалить текущий, установить в nullptr
```

## **Практические примеры использования**

### **Пример 1: Безопасная работа с файлами**
```cpp
#include <memory>
#include <fstream>
#include <vector>

class FileHandler {
    std::unique_ptr<std::fstream> file;
    
public:
    FileHandler(const std::string& filename) 
        : file(std::make_unique<std::fstream>(filename)) {
        
        if (!file->is_open()) {
            throw std::runtime_error("Не удалось открыть файл");
        }
    }
    
    void write(const std::string& data) {
        *file << data;
    }
    
    // Файл автоматически закроется при уничтожении FileHandler
};

int main() {
    try {
        FileHandler handler("data.txt");
        handler.write("Hello, World!");
    } catch (const std::exception& e) {
        std::cerr << "Ошибка: " << e.what() << std::endl;
    }
    // Файл закрыт автоматически
}
```

### **Пример 2: Владеющий контейнер**
```cpp
#include <memory>
#include <vector>
#include <iostream>

class GameObject {
public:
    virtual ~GameObject() = default;
    virtual void update() = 0;
};

class Player : public GameObject {
public:
    void update() override {
        std::cout << "Player обновлен\n";
    }
};

class Enemy : public GameObject {
public:
    void update() override {
        std::cout << "Enemy обновлен\n";
    }
};

class Game {
    std::vector<std::unique_ptr<GameObject>> objects;
    
public:
    void add_object(std::unique_ptr<GameObject> obj) {
        objects.push_back(std::move(obj));
    }
    
    void update_all() {
        for (auto& obj : objects) {
            obj->update();
        }
    }
    
    // Объекты автоматически удаляются при уничтожении вектора
};

int main() {
    Game game;
    
    game.add_object(std::make_unique<Player>());
    game.add_object(std::make_unique<Enemy>());
    
    game.update_all();
    
    return 0;
}
```

### **Пример 3: Кэширование с перемещением**
```cpp
#include <memory>
#include <unordered_map>
#include <string>
#include <iostream>

class ExpensiveResource {
    std::string data;
public:
    ExpensiveResource(const std::string& d) : data(d) {
        std::cout << "Создан ресурс: " << data << std::endl;
    }
    
    ~ExpensiveResource() {
        std::cout << "Удален ресурс: " << data << std::endl;
    }
    
    void use() const {
        std::cout << "Используется: " << data << std::endl;
    }
};

class ResourceCache {
    std::unordered_map<std::string, std::unique_ptr<ExpensiveResource>> cache;
    
public:
    // Получить ресурс (создать или взять из кэша)
    ExpensiveResource* get_resource(const std::string& key) {
        auto it = cache.find(key);
        if (it != cache.end()) {
            return it->second.get();
        }
        
        // Создаем новый ресурс
        auto resource = std::make_unique<ExpensiveResource>(key);
        auto* ptr = resource.get();
        cache[key] = std::move(resource);
        
        return ptr;
    }
    
    // Извлечь ресурс из кэша (передача владения)
    std::unique_ptr<ExpensiveResource> extract_resource(const std::string& key) {
        auto it = cache.find(key);
        if (it == cache.end()) {
            return nullptr;
        }
        
        auto resource = std::move(it->second);
        cache.erase(it);
        return resource;
    }
};
```

## **Правила использования unique_ptr**

### **1. Всегда используйте std::make_unique (C++14+)**
```cpp
// ПЛОХО: потенциальная утечка при исключении
process_widget(std::unique_ptr<Widget>(new Widget), 
               may_throw_function());

// ХОРОШО: безопасно при исключениях
process_widget(std::make_unique<Widget>(), 
               may_throw_function());
```

### **2. Не используйте сырые указатели для владения**
```cpp
// ПЛОХО
Widget* create_widget() {
    return new Widget();  // Кто должен удалять?
}

// ХОРОШО
std::unique_ptr<Widget> create_widget() {
    return std::make_unique<Widget>();  // Ясно, кто владелец
}
```

### **3. Используйте для членов класса**
```cpp
class Document {
    // Владение явное и безопасное
    std::unique_ptr<Header> header;
    std::unique_ptr<Content> content;
    std::unique_ptr<Footer> footer;
    
public:
    Document() 
        : header(std::make_unique<Header>()),
          content(std::make_unique<Content>()),
          footer(std::make_unique<Footer>()) {}
    
    // Правило пяти (Rule of Five) упрощается
    Document(Document&&) = default;
    Document& operator=(Document&&) = default;
    ~Document() = default;
    
    // Копирование требует явной реализации
    Document(const Document& other) 
        : header(other.header ? std::make_unique<Header>(*other.header) : nullptr),
          content(other.content ? std::make_unique<Content>(*other.content) : nullptr),
          footer(other.footer ? std::make_unique<Footer>(*other.footer) : nullptr) {}
};
```

### **4. Возвращайте unique_ptr из фабричных методов**
```cpp
class Shape {
public:
    virtual ~Shape() = default;
    virtual void draw() const = 0;
};

class Circle : public Shape {
public:
    void draw() const override {
        std::cout << "Рисую круг\n";
    }
};

class Square : public Shape {
public:
    void draw() const override {
        std::cout << "Рисую квадрат\n";
    }
};

// Фабрика возвращает unique_ptr
std::unique_ptr<Shape> create_shape(const std::string& type) {
    if (type == "circle") {
        return std::make_unique<Circle>();
    } else if (type == "square") {
        return std::make_unique<Square>();
    }
    return nullptr;
}
```

## **Сравнение с другими умными указателями**

| Особенность | `unique_ptr` | `shared_ptr` | `weak_ptr` |
|------------|--------------|--------------|------------|
| **Владение** | Эксклюзивное | Разделяемое | Без владения |
| **Копирование** | Запрещено | Разрешено | Разрешено |
| **Накладные расходы** | Нет | Счетчик ссылок | Счетчик ссылок |
| **Циклические ссылки** | Нет проблемы | Возможны | Решение проблемы |
| **Использование** | Основной владелец | Разделяемое владение | Наблюдатель |

## **Когда использовать unique_ptr?**

1. **Владение ресурсом в пределах одной области видимости**
2. **Члены класса**, владеющие ресурсами
3. **Возврат из фабричных функций**
4. **Владение в контейнерах STL**
5. **Временное владение в алгоритмах**
6. **Реализация Pimpl идиомы**

### **Пример Pimpl с unique_ptr**
```cpp
// widget.h
class Widget {
    class Impl;
    std::unique_ptr<Impl> pimpl;  // Уникальное владение реализацией
    
public:
    Widget();
    ~Widget();  // Должен быть объявлен (из-за unique_ptr)
    
    Widget(Widget&&);  // Перемещаемый
    Widget& operator=(Widget&&);
    
    // Копирование требует реализации
    Widget(const Widget&);
    Widget& operator=(const Widget&);
    
    void do_something();
};

// widget.cpp
class Widget::Impl {
    int data;
    std::string name;
    
public:
    void process() { /* ... */ }
};

Widget::Widget() : pimpl(std::make_unique<Impl>()) {}
Widget::~Widget() = default;  // Определен здесь, после определения Impl
Widget::Widget(Widget&&) = default;
Widget& Widget::operator=(Widget&&) = default;

void Widget::do_something() {
    pimpl->process();
}
```

## **Вывод**

**`std::unique_ptr`** — это:
1. **Безопасный владелец** динамической памяти
2. **Эффективный** (нулевые накладные расходы)
3. **Явный** в отношении владения
4. **Не копируемый, но перемещаемый**
5. **С настраиваемым удалителем**
6. **Идеальный для большинства случаев владения ресурсами**

**Правило:** Используйте `unique_ptr` по умолчанию для владения динамической памятью. Переходите на `shared_ptr` только когда действительно нужно разделяемое владение.