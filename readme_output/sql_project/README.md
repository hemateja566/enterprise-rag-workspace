# SQL Projects

Collection of SQL database design projects with ER diagrams and schema implementations.

## Projects

### 1. Bookstore Database (`bookstore_db.txt`, `ER_Diagram_bookstore.png`)

Complete database design for an online bookstore.

**Entities:**
- **Customers** - User accounts, addresses, payment methods
- **Books** - Titles, authors, ISBN, categories, pricing, inventory
- **Authors** - Author details, biography
- **Categories** - Genre hierarchy
- **Orders** - Order headers, status, dates
- **Order_Items** - Line items, quantities, prices
- **Reviews** - Customer ratings and reviews
- **Publishers** - Publishing house info
- **Inventory** - Stock levels, warehouse locations

**Key Relationships:**
- Customer 1:N Orders
- Order 1:N Order_Items
- Book N:1 Author
- Book N:1 Publisher
- Book N:M Categories
- Customer 1:N Reviews
- Book 1:N Reviews

**ER Diagram:** `ER_Diagram_bookstore.png`

### 2. Formula 1 Racing Database (`f1_details.txt`, `ER_Diagram_f1racing.png`)

Database for F1 racing statistics and history.

**Entities:**
- **Teams/Constructors** - Team info, nationality, championships
- **Drivers** - Driver details, nationality, DOB, career stats
- **Circuits** - Track info, location, length, corners
- **Races/Grand Prix** - Race events, dates, circuits
- **Seasons** - Championship years
- **Results** - Race results, positions, points, fastest laps
- **Qualifying** - Qualifying session results
- **Pit_Stops** - Pit stop timing and strategy
- **Standings** - Driver/Constructor championship standings

**Key Relationships:**
- Season 1:N Races
- Race 1:N Results
- Driver N:1 Team (per season)
- Race N:1 Circuit
- Result N:1 Driver, N:1 Race, N:1 Team

**ER Diagram:** `ER_Diagram_f1racing.png`

## File Descriptions

| File | Description |
|------|-------------|
| `bookstore_db.txt` | Complete SQL schema (CREATE TABLE, indexes, constraints, sample data) |
| `f1_details.txt` | F1 database schema with sample data |
| `ER_Diagram_bookstore.png` | Visual ER diagram for bookstore |
| `ER_Diagram_f1racing.png` | Visual ER diagram for F1 racing |

## Database Features

### Bookstore
- Normalized to 3NF
- Referential integrity with FK constraints
- Check constraints (price > 0, stock >= 0)
- Indexes on frequently queried columns
- Views for common queries (bestsellers, customer history)
- Stored procedures for order processing
- Triggers for inventory updates

### F1 Racing
- Temporal data modeling (seasonal changes)
- Complex race result calculations
- Historical driver/team transfers
- Circuit configuration changes over time
- Points system evolution handling

## Usage

### MySQL/PostgreSQL

```bash
# Bookstore
mysql -u root -p < bookstore_db.txt

# F1 Racing
mysql -u root -p < f1_details.txt
```

### SQLite

```bash
sqlite3 bookstore.db < bookstore_db.txt
sqlite3 f1.db < f1_details.txt
```

## Sample Queries

### Bookstore - Top Selling Books
```sql
SELECT b.title, a.name as author, SUM(oi.quantity) as total_sold
FROM books b
JOIN authors a ON b.author_id = a.id
JOIN order_items oi ON b.id = oi.book_id
JOIN orders o ON oi.order_id = o.id
WHERE o.status = 'delivered'
GROUP BY b.id, b.title, a.name
ORDER BY total_sold DESC
LIMIT 10;
```

### F1 - Driver Championship Standings
```sql
SELECT d.name, d.nationality, SUM(r.points) as total_points
FROM drivers d
JOIN results r ON d.id = r.driver_id
JOIN races ra ON r.race_id = ra.id
JOIN seasons s ON ra.season_id = s.id
WHERE s.year = 2023
GROUP BY d.id, d.name, d.nationality
ORDER BY total_points DESC;
```

## Tools Used

- **Design**: MySQL Workbench / dbdiagram.io
- **Diagrams**: ER diagrams exported as PNG
- **Testing**: MySQL 8.0 / PostgreSQL 15

## Learning Outcomes

- Entity-relationship modeling
- Normalization (1NF, 2NF, 3NF)
- Constraint design (PK, FK, CHECK, UNIQUE)
- Index optimization
- View creation
- Stored procedures & triggers
- Complex JOIN operations
- Aggregate functions & window functions

## License

MIT License - Educational use encouraged