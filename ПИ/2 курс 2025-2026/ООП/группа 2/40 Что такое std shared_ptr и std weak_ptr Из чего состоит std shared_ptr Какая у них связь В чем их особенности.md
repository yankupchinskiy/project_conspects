# **std::shared_ptr и std::weak_ptr в C++**

## **Введение в совместное владение**

В отличие от `unique_ptr`, который имеет эксклюзивное владение, **`std::shared_ptr`** реализует семантику **совместного владения (shared ownership)** через подсчет ссылок. Несколько `shared_ptr` могут владеть одним и тем же объектом.

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
    // Создание первого shared_ptr
    std::shared_ptr<Resource> ptr1 = std::make_shared<Resource>();
    
    {
        // Второй shared_ptr разделяет владение тем же объектом
        std::shared_ptr<Resource> ptr2 = ptr1;  // Счетчик ссылок: 2
        ptr2->use();
        
        // Третий shared_ptr
        std::shared_ptr<Resource> ptr3 = ptr2;  // Счетчик ссылок: 3
        ptr3->use();
        
        // ptr2 и ptr3 выходят из области видимости
    }  // Счетчик ссылок: 1 (только ptr1)
    
    ptr1->use();
    
    return 0;
}  // Счетчик ссылок: 0 -> объект уничтожается
```

**Вывод:**
```
Ресурс создан
Ресурс используется
Ресурс используется
Ресурс используется
Ресурс уничтожен
```

## **Из чего состоит std::shared_ptr?**

### **Внутренняя структура**
`std::shared_ptr` состоит из **двух указателей**:

1. **Указатель на объект** (raw pointer) — то, что возвращает `get()`
2. **Указатель на управляющий блок (control block)**

### **Управляющий блок содержит:**
```cpp
struct ControlBlock {
    // 1. Счетчик сильных ссылок (strong reference count)
    std::atomic<size_t> strong_ref_count;
    
    // 2. Счетчик слабых ссылок (weak reference count)
    std::atomic<size_t> weak_ref_count;
    
    // 3. Удалитель (deleter) - функция для удаления объекта
    Deleter deleter;
    
    // 4. Аллокатор (allocator) - для удаления управляющего блока
    Allocator allocator;
    
    // 5. Указатель на объект (если не встроен через make_shared)
    T* object_ptr;
};
```

### **Как создается управляющий блок?**
```cpp
// Способ 1: std::make_shared (рекомендуется)
// Создает объект и управляющий блок ВМЕСТЕ в одном выделении памяти
auto ptr1 = std::make_shared<Resource>();

// Способ 2: Конструктор из сырого указателя
// Создает управляющий блок ОТДЕЛЬНО от объекта
std::shared_ptr<Resource> ptr2(new Resource());

// Способ 3: Из другого shared_ptr (копирование)
auto ptr3 = ptr1;  // Использует тот же управляющий блок
```

### **Память при использовании make_shared vs конструктора**
```cpp
// make_shared: ОДНО выделение памяти
// [ Control Block | Объект Resource ]
// ^               ^
// |               |
// ptr1 ---------->|

// Конструктор: ДВА выделения памяти
// [ Control Block ]  [ Объект Resource ]
// ^                  ^
// |                  |
// ptr2 ------------->|
```

## **Особенности std::shared_ptr**

### **1. Подсчет ссылок (Reference Counting)**
```cpp
#include <memory>
#include <iostream>

void print_ref_count(const std::shared_ptr<int>& sp, const std::string& name) {
    std::cout << name << " use_count: " << sp.use_count() << std::endl;
}

int main() {
    auto sp1 = std::make_shared<int>(42);
    print_ref_count(sp1, "sp1");  // 1
    
    {
        auto sp2 = sp1;  // Копирование
        print_ref_count(sp1, "sp1");  // 2
        print_ref_count(sp2, "sp2");  // 2
        
        auto sp3 = sp2;  // Еще одно копирование
        print_ref_count(sp1, "sp1");  // 3
    }  // sp2 и sp3 уничтожаются
    
    print_ref_count(sp1, "sp1");  // 1
    
    sp1.reset();  // Явный сброс
    print_ref_count(sp1, "sp1");  // 0
}
```

### **2. Циклические ссылки (Cyclic References) — ПРОБЛЕМА!**
```cpp
#include <memory>
#include <iostream>

class Node {
public:
    std::shared_ptr<Node> next;
    std::string name;
    
    Node(const std::string& n) : name(n) {
        std::cout << "Создан узел: " << name << std::endl;
    }
    
    ~Node() {
        std::cout << "Уничтожен узел: " << name << std::endl;
    }
};

int main() {
    // Циклическая ссылка
    auto node1 = std::make_shared<Node>("A");
    auto node2 = std::make_shared<Node>("B");
    
    node1->next = node2;  // A указывает на B
    node2->next = node1;  // B указывает на A (ЦИКЛ!)
    
    // При выходе из области видимости:
    // 1. node1.use_count() = 2 (node1 + node2->next)
    // 2. node2.use_count() = 2 (node2 + node1->next)
    // 3. Ни один из узлов НЕ будет уничтожен! УТЕЧКА ПАМЯТИ!
    
    std::cout << "node1 use_count: " << node1.use_count() << std::endl;  // 2
    std::cout << "node2 use_count: " << node2.use_count() << std::endl;  // 2
    
    return 0;
}  // Утечка памяти!
```

## **std::weak_ptr — решение проблемы циклических ссылок**

### **Что такое std::weak_ptr?**
`std::weak_ptr` — это "слабая" (weak) ссылка на объект, управляемый `shared_ptr`. Она:
1. **Не увеличивает счетчик ссылок**
2. **Не препятствует удалению объекта**
3. **Позволяет проверить, жив ли объект**

### **Как использовать weak_ptr?**
```cpp
#include <memory>
#include <iostream>

class Resource {
public:
    Resource() { std::cout << "Ресурс создан\n"; }
    ~Resource() { std::cout << "Ресурс уничтожен\n"; }
};

int main() {
    // Создаем shared_ptr
    std::shared_ptr<Resource> sp = std::make_shared<Resource>();
    std::cout << "use_count: " << sp.use_count() << std::endl;  // 1
    
    // Создаем weak_ptr из shared_ptr
    std::weak_ptr<Resource> wp = sp;
    std::cout << "use_count после weak_ptr: " << sp.use_count() << std::endl;  // 1
    
    // Проверяем, жив ли объект
    if (!wp.expired()) {
        std::cout << "Объект еще жив\n";
    }
    
    // Получаем shared_ptr из weak_ptr (если объект жив)
    if (auto locked = wp.lock()) {
        std::cout << "Успешно заблокировали weak_ptr\n";
        std::cout << "use_count после lock: " << sp.use_count() << std::endl;  // 2
    }
    
    // Уничтожаем исходный shared_ptr
    sp.reset();
    std::cout << "use_count после reset: " << sp.use_count() << std::endl;  // 0
    
    // Проверяем weak_ptr
    if (wp.expired()) {
        std::cout << "Объект уничтожен\n";
    }
    
    auto locked = wp.lock();
    if (!locked) {
        std::cout << "Не удалось получить shared_ptr - объект мертв\n";
    }
}
```

### **Решение проблемы циклических ссылок с weak_ptr**
```cpp
#include <memory>
#include <iostream>

class Node;

class Node {
public:
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> prev;  // Используем weak_ptr для обратной ссылки
    std::string name;
    
    Node(const std::string& n) : name(n) {
        std::cout << "Создан узел: " << name << std::endl;
    }
    
    ~Node() {
        std::cout << "Уничтожен узел: " << name << std::endl;
    }
    
    void set_previous(const std::shared_ptr<Node>& node) {
        prev = node;  // weak_ptr не увеличивает счетчик
    }
    
    std::shared_ptr<Node> get_previous() const {
        return prev.lock();  // Получаем shared_ptr, если объект жив
    }
};

int main() {
    auto node1 = std::make_shared<Node>("A");
    auto node2 = std::make_shared<Node>("B");
    
    node1->next = node2;      // A -> B (сильная ссылка)
    node2->set_previous(node1); // B -> A (слабая ссылка!)
    
    std::cout << "node1 use_count: " << node1.use_count() << std::endl;  // 1
    std::cout << "node2 use_count: " << node2.use_count() << std::endl;  // 2
    
    // При выходе из области видимости:
    // 1. node1.use_count() = 1 (только node1)
    // 2. node2.use_count() = 2 (node2 + node1->next)
    // 3. node1 уничтожается (use_count становится 0)
    // 4. node1->next уничтожается, node2.use_count() = 1
    // 5. node2 уничтожается (use_count становится 0)
    
    return 0;  // Все узлы корректно уничтожаются
}
```

## **Связь между shared_ptr и weak_ptr**

### **1. Иерархия ссылок**
```
        shared_ptr A      shared_ptr B
           |                  |
           v                  v
[Control Block] -strong-> [Объект]
     |  ^
weak |  | strong
     v  |
   weak_ptr
```

### **2. Правила работы счетчиков**
```cpp
auto sp = std::make_shared<int>(42);  // strong_ref = 1, weak_ref = 0

std::weak_ptr<int> wp1 = sp;  // strong_ref = 1, weak_ref = 1
std::weak_ptr<int> wp2 = sp;  // strong_ref = 1, weak_ref = 2

{
    auto sp2 = sp;            // strong_ref = 2, weak_ref = 2
    auto sp3 = wp1.lock();    // strong_ref = 3, weak_ref = 2
}                             // strong_ref = 1, weak_ref = 2

sp.reset();                   // strong_ref = 0, weak_ref = 2
                              // Объект УДАЛЯЕТСЯ, но управляющий блок еще жив
                              // weak_ref = 2 (weak_ptr все еще существуют)

wp1.reset();                  // weak_ref = 1
wp2.reset();                  // weak_ref = 0
                              // Теперь управляющий блок тоже удаляется
```

## **Особенности и нюансы**

### **1. Потокобезопасность**
```cpp
#include <memory>
#include <thread>
#include <vector>
#include <iostream>

// shared_ptr: атомарные операции с счетчиком ссылок
// Но доступ к самому объекту НЕ синхронизирован!

std::shared_ptr<int> global_ptr = std::make_shared<int>(0);

void increment(int n) {
    for (int i = 0; i < n; ++i) {
        // Безопасно: операции с счетчиком ссылок
        auto local_copy = global_ptr;
        
        // ОПАСНО: изменение объекта не синхронизировано
        (*local_copy)++;
    }
}

int main() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back(increment, 1000);
    }
    
    for (auto& t : threads) {
        t.join();
    }
    
    std::cout << "Result: " << *global_ptr << std::endl;  // Непредсказуемо
}
```

### **2. Производительность**
```cpp
// shared_ptr дороже unique_ptr:
// 1. Дополнительная память для управляющего блока
// 2. Атомарные операции с счетчиками (медленнее)
// 3. Два разыменования указателя вместо одного

// unique_ptr: быстрый, минимальные накладные расходы
// shared_ptr: медленнее в 2-3 раза из-за подсчета ссылок
```

### **3. enable_shared_from_this**
```cpp
#include <memory>
#include <iostream>

class Widget : public std::enable_shared_from_this<Widget> {
public:
    std::shared_ptr<Widget> get_shared() {
        return shared_from_this();  // Безопасно получить shared_ptr
    }
    
    // НЕ ДЕЛАЙТЕ ТАК!
    std::shared_ptr<Widget> get_unsafe() {
        return std::shared_ptr<Widget>(this);  // Создаст новый управляющий блок!
    }
};

int main() {
    auto w1 = std::make_shared<Widget>();
    
    auto w2 = w1->get_shared();  // OK: use_count = 2
    std::cout << "use_count: " << w1.use_count() << std::endl;  // 2
    
    // ОПАСНО: двойное удаление!
    // auto w3 = w1->get_unsafe();  // Неопределенное поведение!
    
    return 0;
}
```

### **4. Пользовательские удалители и аллокаторы**
```cpp
#include <memory>
#include <iostream>

// Пользовательский удалитель
struct FileDeleter {
    void operator()(FILE* f) const {
        if (f) {
            fclose(f);
            std::cout << "Файл закрыт пользовательским удалителем\n";
        }
    }
};

int main() {
    // shared_ptr с пользовательским удалителем
    std::shared_ptr<FILE> file(
        fopen("test.txt", "w"),
        FileDeleter()
    );
    
    // Можно использовать make_shared с пользовательским удалителем
    // (но только через allocate_shared)
    
    return 0;
}
```

## **Практические паттерны использования**

### **1. Кэширование объектов**
```cpp
#include <memory>
#include <unordered_map>
#include <iostream>
#include <string>

class ExpensiveObject {
    std::string data;
public:
    ExpensiveObject(const std::string& key) : data("data_for_" + key) {
        std::cout << "Создан объект для ключа: " << key << std::endl;
    }
    
    ~ExpensiveObject() {
        std::cout << "Уничтожен объект\n";
    }
    
    void use() const {
        std::cout << "Используем: " << data << std::endl;
    }
};

class Cache {
    std::unordered_map<std::string, std::weak_ptr<ExpensiveObject>> cache;
    
public:
    std::shared_ptr<ExpensiveObject> get(const std::string& key) {
        auto it = cache.find(key);
        
        // Если есть weak_ptr в кэше
        if (it != cache.end()) {
            // Пробуем получить shared_ptr
            auto shared = it->second.lock();
            if (shared) {
                std::cout << "Кэш попадание для: " << key << std::endl;
                return shared;  // Объект еще жив
            } else {
                // Объект был удален, удаляем запись
                cache.erase(it);
            }
        }
        
        // Создаем новый объект
        std::cout << "Кэш промах для: " << key << ", создаем новый\n";
        auto shared = std::make_shared<ExpensiveObject>(key);
        cache[key] = shared;  // Сохраняем weak_ptr
        
        return shared;
    }
};

int main() {
    Cache cache;
    
    {
        auto obj1 = cache.get("user_1");
        obj1->use();
        
        auto obj2 = cache.get("user_1");  // Возьмет из кэша
        obj2->use();
    }  // obj1 и obj2 уничтожаются, объект удаляется
    
    auto obj3 = cache.get("user_1");  // Придется создать заново
    obj3->use();
}
```

### **2. Наблюдатели (Observers)**
```cpp
#include <memory>
#include <vector>
#include <iostream>
#include <algorithm>

class Observer : public std::enable_shared_from_this<Observer> {
    std::string name;
public:
    Observer(const std::string& n) : name(n) {}
    
    void notify(const std::string& message) {
        std::cout << name << " получил: " << message << std::endl;
    }
    
    std::weak_ptr<Observer> get_weak() {
        return weak_from_this();
    }
};

class Subject {
    std::vector<std::weak_ptr<Observer>> observers;
    
public:
    void add_observer(const std::shared_ptr<Observer>& obs) {
        observers.push_back(obs->get_weak());
    }
    
    void notify_all(const std::string& message) {
        // Удаляем "мертвые" weak_ptr
        observers.erase(
            std::remove_if(observers.begin(), observers.end(),
                [](const std::weak_ptr<Observer>& wp) {
                    return wp.expired();
                }),
            observers.end()
        );
        
        // Уведомляем живых наблюдателей
        for (auto& weak_obs : observers) {
            if (auto obs = weak_obs.lock()) {
                obs->notify(message);
            }
        }
    }
};
```

### **3. Графы с shared_ptr и weak_ptr**
```cpp
#include <memory>
#include <vector>
#include <iostream>

class GraphNode : public std::enable_shared_from_this<GraphNode> {
    std::vector<std::shared_ptr<GraphNode>> children;
    std::vector<std::weak_ptr<GraphNode>> parents;  // weak_ptr для родителей
    std::string name;
    
public:
    GraphNode(const std::string& n) : name(n) {
        std::cout << "Создан узел: " << name << std::endl;
    }
    
    ~GraphNode() {
        std::cout << "Уничтожен узел: " << name << std::endl;
    }
    
    void add_child(const std::shared_ptr<GraphNode>& child) {
        children.push_back(child);
        child->add_parent(shared_from_this());
    }
    
    void add_parent(const std::shared_ptr<GraphNode>& parent) {
        parents.push_back(parent);  // weak_ptr - не увеличивает счетчик
    }
    
    void print_tree(int depth = 0) const {
        std::cout << std::string(depth * 2, ' ') << name << std::endl;
        for (const auto& child : children) {
            child->print_tree(depth + 1);
        }
    }
};
```

## **Правила использования**

### **Когда использовать shared_ptr?**
1. **Разделяемое владение** несколькими объектами
2. **Возврат из фабрик**, когда владение должно быть разделяемым
3. **Кэширование** объектов
4. **Наблюдатели и подписчики**
5. **Сложные структуры данных** (графы, деревья)

### **Когда использовать weak_ptr?**
1. **Разрыв циклических ссылок**
2. **Кэширование** (для отслеживания объектов без продления их жизни)
3. **Наблюдатели** (ссылки на субъекты)
4. **Временные ссылки** без передачи владения

### **Чего избегать?**
```cpp
// 1. НЕ создавайте несколько shared_ptr из одного сырого указателя
int* raw = new int(42);
std::shared_ptr<int> sp1(raw);
// std::shared_ptr<int> sp2(raw);  // КАТАСТРОФА! Двойное удаление!

// 2. НЕ используйте shared_ptr, если достаточно unique_ptr
// unique_ptr быстрее и понятнее для эксклюзивного владения

// 3. НЕ создавайте shared_ptr в критичных по производительности участках

// 4. НЕ передавайте shared_ptr по значению без необходимости
void process_good(const std::shared_ptr<Resource>& sp);  // ✓
void process_bad(std::shared_ptr<Resource> sp);          // ✗ (лишнее копирование)
```

## **Сравнительная таблица**

| Характеристика | `unique_ptr` | `shared_ptr` | `weak_ptr` |
|----------------|--------------|--------------|------------|
| **Владение** | Эксклюзивное | Разделяемое | Без владения |
| **Копирование** | Запрещено | Разрешено | Разрешено |
| **Перемещение** | Разрешено | Разрешено | Разрешено |
| **Счетчик ссылок** | Нет | Есть (strong) | Есть (weak) |
| **Размер** | 1 указатель | 2 указателя | 2 указателя |
| **Производительность** | Максимальная | Средняя (атомарные операции) | Средняя |
| **Циклические ссылки** | Не проблема | Проблема | Решение |
| **Основное назначение** | Единственный владелец | Совместное владение | Наблюдение без владения |

## **Вывод**

**`std::shared_ptr`** и **`std::weak_ptr`** — мощные инструменты для управления памятью:
- **`shared_ptr`** обеспечивает безопасное разделяемое владение через подсчет ссылок
- **`weak_ptr`** решает проблему циклических ссылок и позволяет наблюдать за объектами без продления их жизни
- Используйте **`make_shared`** для эффективного выделения памяти
- Всегда помните о **проблеме циклических ссылок** и используйте **`weak_ptr`** для их разрыва
- Используйте **`enable_shared_from_this`** для безопасного получения `shared_ptr` из метода объекта