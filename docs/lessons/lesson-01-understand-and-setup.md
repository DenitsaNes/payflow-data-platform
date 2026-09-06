# Lesson 1: Understand PayFlow and Set Up MySQL

> Welcome. This lesson is for absolute beginners. We will go slowly.

---

## 1. The story: What is PayFlow?

Imagine a company called **PayFlow**. PayFlow helps online shops accept payments. When you buy something from a shop that uses PayFlow, your money does not go directly to PayFlow. It goes through an external company called a **payment provider** or **payment gateway**.

PayFlow works with three payment providers:

- **Provider A** sends a CSV file every day.
- **Provider B** sends a JSON file every day.
- **Provider C** sends a different CSV file every day.

Each provider uses different column names. For example:

| Provider A | Provider B | Provider C |
|------------|------------|------------|
| `transaction_id` | `payment_id` | `transactionId` |
| `amount` | `value` | `amount` |
| `status` | `payment_status` | `result` |

PayFlow also has its own internal system that records every transaction.

### The problem

Every morning, the finance team downloads these files and compares them manually. This takes 4 hours and is full of mistakes.

### Our job as data engineers

We will build a system that:

1. **Ingests** the files automatically.
2. **Transforms** them into one common format.
3. **Checks quality** (duplicates, bad amounts, wrong currencies).
4. **Reconciles** provider data against PayFlow's internal records.
5. **Calculates billing** for each merchant.
6. **Shows results** in a dashboard.

This is exactly what junior data engineers do at companies like Accedia.

---

## 2. The tools we will use

| Tool | What it does | Why we use it |
|------|--------------|---------------|
| **MySQL** | Stores data in tables. | It is a relational database. We use SQL to query it. |
| **SQL** | The language we use to ask MySQL questions. | It is the most important skill for a data engineer. |
| **Python** | A programming language for moving and cleaning data. | We will use it to read CSV/JSON files and load them into MySQL. |
| **Docker** | Runs MySQL inside a "container" on your laptop. | You do not need to install MySQL directly. Docker keeps everything isolated. |
| **GitHub** | Stores your code online. | Recruiters and interviewers can see your project. |

---

## 3. Why MySQL?

MySQL is a **relational database**. It stores data in tables with rows and columns.

We chose MySQL because:

- It is very popular.
- It uses standard SQL.
- It is great for learning.
- Many companies use it.

> **Important:** MySQL is similar to PostgreSQL, SQL Server, and Oracle. Once you know MySQL SQL, the others are easy to learn.

---

## 4. Before we start: install the tools

### A. Docker Desktop

Docker lets us run MySQL on your computer without installing it directly.

1. Go to https://www.docker.com/products/docker-desktop/
2. Download Docker Desktop for your operating system.
3. Install it.
4. Open Docker Desktop.
5. Wait until it says "Engine running".

> **Why?** Docker Desktop is the program that starts and manages containers. A container is like a small computer inside your computer.

### B. MySQL client

The MySQL client is a command-line tool that lets you talk to MySQL.

#### On macOS (using Homebrew)

```bash
brew install mysql-client
```

After installation, you may need to add it to your path:

```bash
echo 'export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### On Windows

Download MySQL Shell or MySQL Community Server from https://dev.mysql.com/downloads/

#### On Linux

```bash
sudo apt-get update
sudo apt-get install mysql-client
```

### C. Verify installations

Open your terminal and run:

```bash
docker --version
mysql --version
```

You should see version numbers. If you see "command not found", the tool is not installed correctly.

---

## 5. Start the project folder

Open your terminal and move into the PayFlow folder:

```bash
cd payflow-data-platform
```

> **What is this folder?** It contains the whole project: SQL files, Python files, sample data, and documentation.

---

## 6. Start MySQL with Docker

> **Note about ports:** If you already have MySQL installed on your Mac, it is probably using port `3306`. To avoid a conflict, this project uses port `3307` on your Mac and forwards it to port `3306` inside the Docker container. That is why all commands below include `-P 3307`.

We already prepared a file called `docker-compose.yml`. This file tells Docker how to start MySQL.

Run this command:

```bash
docker compose up -d
```

> **What does this do?**
>
> - `docker compose` reads the `docker-compose.yml` file.
> - `up` starts the services inside it.
> - `-d` means "run in the background" (detached).

Wait about 15 seconds for MySQL to fully start.

### Check if it is running

```bash
docker ps
```

You should see a container named `payflow-mysql`.

---

## 7. Create the database and tables

We wrote the database structure for you in:

```text
sql/schema/01_create_database.sql
```

This file creates:

- The `payflow` database.
- Staging tables (where we first put raw data).
- Dimension tables (like `dim_merchant`, `dim_date`).
- Fact tables (like `fact_transaction`, `fact_reconciliation`).
- Reconciliation helper tables.
- Indexes to make queries faster.
- Seed data for currencies, providers, and statuses.

Run it:

```bash
mysql -h localhost -P 3307 -u payflow -p payflow < sql/schema/01_create_database.sql
```

> **What does this command mean?**
>
> - `mysql` — the MySQL client program.
> - `-h localhost` — connect to the database on this computer.
> - `-u payflow` — username is `payflow`.
> - `-p` — ask for a password.
> - `payflow` — the database name.
> - `< sql/schema/01_create_database.sql` — take the contents of this file and send it to MySQL.

When it asks for a password, type:

```text
payflow
```

> **Note:** When you type the password, nothing will appear on screen. This is normal for security.

If everything works, you will see no error.

---

## 8. Seed sample data

Now we load some sample internal transactions and merchants:

```bash
mysql -h localhost -P 3307 -u payflow -p payflow < data/sample/seed_data.sql
```

Again, password is `payflow`.

---

## 9. Connect to MySQL and look around

Now let's open the MySQL command line:

```bash
mysql -h localhost -P 3307 -u payflow -p payflow
```

You are now inside MySQL. Your prompt will look like:

```text
mysql>
```

### See all tables

Run:

```sql
SHOW TABLES;
```

You should see many tables starting with `warehouse_`, `staging_`, and `reconciliation_`.

### Look at the merchants

```sql
SELECT * FROM warehouse_dim_merchant;
```

You should see three merchants: M001, M002, M003.

### Look at the internal transactions

```sql
SELECT * FROM reconciliation_internal_transactions;
```

You should see 11 transactions.

### Exit MySQL

```sql
EXIT;
```

---

## 10. What did we just do?

| Step | What happened | Why it matters |
|------|---------------|----------------|
| Started Docker | MySQL is now running on your computer | We need a database to store data |
| Created tables | Defined the structure of our warehouse | Data needs organization |
| Seeded data | Added sample merchants and transactions | We need something to practice with |
| Connected with client | We can now run SQL queries | This is how data engineers work |

---

## 11. Common problems

### "Cannot connect to Docker daemon"

**Cause:** Docker Desktop is not running.

**Fix:** Open Docker Desktop and wait until it says "Engine running". Then try again.

### "Access denied for user 'payflow'"

**Cause:** Wrong password or the container did not initialize yet.

**Fix:** Wait 15 seconds and try again. Make sure you typed `payflow` as the password.

### "Unknown database 'payflow'"

**Cause:** The schema file did not run correctly.

**Fix:** Re-run the schema file:

```bash
mysql -h localhost -P 3307 -u payflow -p payflow < sql/schema/01_create_database.sql
```

### "mysql command not found"

**Cause:** MySQL client is not installed or not in your path.

**Fix:** Reinstall `mysql-client` and follow the path instructions above.

---

## 12. Your homework before Lesson 2

1. Make sure Docker Desktop is installed and running.
2. Install the MySQL client.
3. Run `docker compose up -d` inside the project folder.
4. Run the schema file.
5. Run the seed data file.
6. Connect with `mysql -h localhost -P 3307 -u payflow -p payflow` and run `SHOW TABLES;`.
7. Look at `warehouse_dim_merchant` and `reconciliation_internal_transactions`.

If any step fails, tell me the exact error message and I will help you fix it.

---

## 13. What is next?

In **Lesson 2**, we will:

- Explore the provider files (CSV and JSON).
- Understand the differences between them.
- Learn about the star schema we built.
- Run more SQL queries.

See you there.
