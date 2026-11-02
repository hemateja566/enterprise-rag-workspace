# Midas - JPMC Advanced Software Engineering Forage Program

Project repository for the JPMorgan Chase & Co. Advanced Software Engineering Virtual Experience Program on Forage.

## About

This is a fork of the official JPMC Forage program repository. It contains solutions and implementations for the Advanced Software Engineering virtual internship tasks.

## Program Details

- **Program**: JPMC Advanced Software Engineering
- **Platform**: Forage (The Vault)
- **Focus**: Backend development, system design, API development

## Project Structure

```
forage-midas/
├── src/                    # Main source code
│   └── main/java/          # Java source files
├── services/               # Service implementations
├── .mvn/                   # Maven wrapper
├── pom.xml                 # Maven project configuration
├── application.yml         # Spring Boot configuration
├── mvnw                    # Maven wrapper script (Unix)
├── mvnw.cmd                # Maven wrapper script (Windows)
└── README.md               # This file
```

## Technology Stack

- **Language**: Java 17+
- **Framework**: Spring Boot
- **Build Tool**: Maven
- **Database**: H2 (in-memory) / PostgreSQL
- **Testing**: JUnit 5, Mockito

## Getting Started

### Prerequisites

- Java 17 or higher
- Maven 3.8+ (or use included wrapper)

### Running the Application

Using Maven wrapper:
```bash
# Unix/macOS
./mvnw spring-boot:run

# Windows
mvnw.cmd spring-boot:run
```

Or with Maven directly:
```bash
mvn spring-boot:run
```

### Building

```bash
./mvnw clean package
```

### Running Tests

```bash
./mvnw test
```

## Configuration

Edit `application.yml` for:
- Database configuration
- Server port
- Logging levels
- External API keys

## Tasks Completed

- [ ] Task 1: System Design
- [ ] Task 2: API Development
- [ ] Task 3: Data Processing
- [ ] Task 4: Testing & Documentation

## Resources

- [Forage JPMC Program](https://www.theforage.com/virtual-internships/prototype/jpmorgan/adw9)
- [Spring Boot Documentation](https://spring.io/projects/spring-boot)
- [Maven Documentation](https://maven.apache.org/guides/index.html)

## License

This project is for educational purposes as part of the Forage virtual experience program.