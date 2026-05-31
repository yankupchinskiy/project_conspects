## **Гарантии исключений (Exception Guarantees)**

Гарантии исключений — это уровни безопасности, которые функции предоставляют относительно поведения при исключениях. Они образуют иерархию от самых строгих к самым слабым.

### **1. Гарантия отсутствия исключений (No-throw Guarantee)**
**Самая строгая гарантия.** Функция никогда не выбрасывает исключения.

```cpp
// Примеры с гарантией отсутствия исключений:
void simple_swap(int& a, int& b) noexcept {
    int temp = a;
    a = b;
    b = temp;
    // Никаких операций, которые могут бросить исключение
}

// Деструкторы по умолчанию имеют noexcept
class Resource {
public:
    ~Resource() noexcept = default;  // Неявно и так noexcept
};
```

**Характеристики:**
- Функция помечается `noexcept`
- При нарушении гарантии вызывается `std::terminate()`
- Требуется для многих операций в STL

### **2. Строгая гарантия исключений (Strong Exception Guarantee)**
**Транзакционная гарантия.** Если функция выбрасывает исключение, состояние программы остается неизменным (как будто функция не вызывалась).

```cpp
class Account {
    double balance;
public:
    // Строгая гарантия: либо перевод успешен, либо ничего не меняется
    void transfer_funds(Account& to, double amount) {
        Account old_this = *this;      // Сохраняем состояние
        Account old_to = to;
        
        try {
            this->balance -= amount;   // Может бросить исключение?
            to.balance += amount;      // Может бросить исключение?
        }
        catch (...) {
            // Откат изменений
            *this = std::move(old_this);
            to = std::move(old_to);
            throw;  // Пробрасываем исключение дальше
        }
    }
};

// В STL: vector::push_back обеспечивает строгую гарантию
// (если конструктор перемещения/копирования элемента не бросает исключений)
std::vector<int> v;
v.push_back(42);  // Если память не выделится, вектор останется в исходном состоянии
```

**Характеристики:**
- Либо полный успех, либо полный откат
- Реализуется через copy-and-swap идиому
- Самый безопасный, но часто самый дорогой вариант

### **3. Базовая гарантия исключений (Basic Exception Guarantee)**
**Минимальная безопасность.** При исключении программа остается в консистентном состоянии (нет утечек ресурсов), но состояние объектов может измениться.

```cpp
class Database {
    Connection* conn;
    std::vector<Query> pending_queries;
public:
    void execute_batch() {
        for (auto& query : pending_queries) {
            conn->execute(query);  // Может бросить исключение
            // Если исключение здесь, некоторые запросы уже выполнены
            // Но ресурсы корректно освобождены
        }
        pending_queries.clear();  // Не выполнится при исключении
    }
    
    ~Database() {
        delete conn;  // Гарантированно освобождает ресурсы
    }
};
```

**Характеристики:**
- Нет утечек ресурсов
- Сохраняются инварианты класса
- Но состояние может отличаться от исходного

### **4. Отсутствие гарантии (No Guarantee)**
**Самая слабая.** Функция может оставить программу в неопределенном состоянии при исключении.

```cpp
// ПЛОХОЙ ПРИМЕР - нет гарантий
void unsafe_operation(int*& ptr, size_t new_size) {
    delete[] ptr;           // Освобождаем старую память
    ptr = new int[new_size];  // Может бросить std::bad_alloc
    // Если исключение здесь, ptr указывает на освобожденную память!
}
```

## **Сравнение гарантий**

| Гарантия | Состояние программы | Утечки ресурсов | Производительность | Примеры использования |
|----------|-------------------|----------------|-------------------|----------------------|
| **No-throw** | Не меняется | Нет | Высокая | Деструкторы, освобождение ресурсов, swap |
| **Strong** | Восстанавливается | Нет | Низкая (копирование) | Транзакции, важные операции |
| **Basic** | Консистентное, но измененное | Нет | Средняя | Большинство операций |
| **No guarantee** | Неопределенное | Возможны | Высокая | Устаревший код, низкоуровневые операции |

## **Ключевое слово `noexcept`**

### **1. Что такое `noexcept`?**

`noexcept` — это спецификатор (C++11 и выше), указывающий, что функция **не бросает исключений**. Это более мощная замена устаревшему `throw()`.

```cpp
// Старый стиль (C++98) - не рекомендуется
void old_func() throw();  // Устарело

// Новый стиль (C++11+)
void new_func() noexcept;  // Рекомендуется
```

### **2. Зачем нужно `noexcept`?**

#### **а) Оптимизация**
Компилятор может генерировать более эффективный код:
```cpp
std::vector<MyType> v;
// Если перемещающий конструктор MyType - noexcept,
// vector будет использовать его при реаллокации.
// Иначе - будет использовать копирующий конструктор (медленнее).
```

#### **б) Контракт и документация**
```cpp
void cleanup() noexcept;  // Явно говорит: "я не брошу исключение"
```

#### **в) Безопасность в определенных контекстах**
```cpp
// Деструкторы по умолчанию noexcept
// Исключение в деструкторе = std::terminate()
```

### **3. Синтаксис `noexcept`**

```cpp
// 1. Безусловный noexcept
void func1() noexcept;           // Не бросает исключений
void func2() noexcept(true);     // То же самое

// 2. Условный noexcept
template<typename T>
void swap(T& a, T& b) noexcept(noexcept(T(std::move(a))) && 
                                noexcept(a.operator=(std::move(b)))) {
    // noexcept зависит от операций перемещения T
}

// 3. Оператор noexcept (проверяет, является ли выражение noexcept)
bool is_noexcept = noexcept(func1());  // true
```

### **4. Особенности применения**

#### **а) Деструкторы**
```cpp
class Resource {
public:
    ~Resource() noexcept {  // Явно указано (но и так по умолчанию)
        // НИКОГДА не бросайте исключения здесь!
        // Иначе вызовется std::terminate()
    }
};
```

#### **б) Перемещающие операции**
```cpp
class Buffer {
    int* data;
    size_t size;
public:
    // Перемещающий конструктор - хороший кандидат для noexcept
    Buffer(Buffer&& other) noexcept 
        : data(other.data), size(other.size) {
        other.data = nullptr;
        other.size = 0;
    }
    
    // Перемещающий оператор присваивания
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data;          // noexcept
            data = other.data;      // noexcept
            size = other.size;      // noexcept
            other.data = nullptr;   // noexcept
            other.size = 0;         // noexcept
        }
        return *this;
    }
};
```

#### **в) Виртуальные функции**
```cpp
class Base {
public:
    virtual void foo() noexcept;  // Все переопределения должны быть noexcept
};

class Derived : public Base {
public:
    void foo() noexcept override;  // OK
    // void foo() override;        // Ошибка: нет noexcept
};
```

### **5. Проверка `noexcept` во время компиляции**

```cpp
#include <type_traits>

struct MyType {
    MyType(MyType&&) noexcept;
    MyType& operator=(MyType&&) noexcept;
};

// Проверка типа
static_assert(std::is_nothrow_move_constructible<MyType>::value, 
              "MyType должен иметь noexcept перемещающий конструктор");

// Проверка выражения
constexpr bool can_swap = noexcept(
    std::declval<MyType&>().swap(std::declval<MyType&>())
);
```

### **6. `noexcept` в стандартной библиотеке**

```cpp
// Многие алгоритмы STL требуют noexcept для оптимизации
std::vector<int> v1, v2;
// Если перемещающий конструктор int noexcept, будет использоваться перемещение
v1 = std::move(v2);

// std::move_if_noexcept выбирает между копированием и перемещением
template<class T>
typename std::conditional<
    !std::is_nothrow_move_constructible<T>::value &&
    std::is_copy_constructible<T>::value,
    const T&, T&&>::type
move_if_noexcept(T& x) noexcept;
```

## **Практические рекомендации**

### **Когда использовать `noexcept`?**

1. **Всегда для деструкторов** (они и так по умолчанию `noexcept`)
2. **Для простых функций-оберток**
   ```cpp
   int get_value() const noexcept { return value; }
   void set_value(int v) noexcept { value = v; }
   ```
3. **Для перемещающих операций**, если они действительно безопасны
4. **Для функций освобождения ресурсов**
   ```cpp
   void close() noexcept;
   void release() noexcept;
   ```
5. **Для функций обмена (swap)**
   ```cpp
   void swap(MyClass& other) noexcept {
       using std::swap;
       swap(data, other.data);
   }
   ```

### **Когда НЕ использовать `noexcept`?**

1. **Функции, которые могут бросить исключения**
2. **Функции, вызывающие другие функции без `noexcept`**
3. **Когда сомневаетесь** (лучше безопасность, чем производительность)

### **Шаблон проектирования с гарантиями**

```cpp
class Transaction {
    std::vector<Operation> operations;
    Database& db;
    
public:
    // Строгая гарантия: либо все операции выполнены, либо ни одной
    void commit() {
        auto backup = db.create_backup();  // Сохраняем состояние
        
        try {
            for (auto& op : operations) {
                db.execute(op);  // Может бросить исключение
            }
        }
        catch (...) {
            db.restore(backup);  // Откат к сохраненному состоянию
            throw;  // Пробрасываем исключение дальше
        }
        
        operations.clear();  // Только если все успешно
    }
    
    // Базовая гарантия: добавляем операцию
    void add_operation(const Operation& op) {
        operations.push_back(op);  // Может бросить std::bad_alloc
        // Если исключение, операции остаются в консистентном состоянии
    }
    
    // No-throw гарантия
    void clear() noexcept {
        operations.clear();  // vector::clear() гарантированно не бросает
    }
    
    ~Transaction() noexcept = default;  // Деструктор - noexcept
};
```

## **Выводы**

1. **Гарантии исключений** — это уровни безопасности, которые вы предоставляете пользователям вашего кода.
2. **Стремитесь к самой строгой гарантии**, которую можете обеспечить разумно.
3. **`noexcept`** — это не просто оптимизация, это контракт с компилятором и пользователями.
4. **Используйте `noexcept` осознанно** — обещание "не бросать исключения" должно выполняться.
5. **Деструкторы всегда должны быть `noexcept`** — это фундаментальное правило C++.

Правильное использование гарантий исключений и `noexcept` делает ваш код:
- **Более безопасным** (предсказуемое поведение при ошибках)
- **Более эффективным** (возможности для оптимизации)
- **Более понятным** (явные контракты)
- **Более совместимым** со стандартной библиотекой C++