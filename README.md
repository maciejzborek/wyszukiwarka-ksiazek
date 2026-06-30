# Book Search API

Prosta aplikacja REST API do wyszukiwania książek po tytule, korzystająca z [OpenLibrary.org](https://openlibrary.org).

## Opis projektu

API udostępnia trzy endpointy:
- `GET /health` – sprawdzenie stanu aplikacji
- `GET /version` – zwraca wersję aplikacji
- `GET /search?title=<tytuł>&limit=<n>` – wyszukuje książki w OpenLibrary.org

## Architektura

```
GitHub → GitHub Actions → Amazon ECR → Amazon EC2 (t3.micro, Amazon Linux 2023)
                                              ↓
                                     Nginx (port 80)
                                              ↓
                                    FastAPI app (port 8000)
                                              ↓
                                     CloudWatch Logs
```

Na EC2 działają dwa kontenery Docker zarządzane przez docker-compose:
- **nginx** – reverse proxy, przyjmuje ruch na porcie 80
- **app** – FastAPI na porcie 8000 (niewidoczny z zewnątrz)

## Wymagania lokalne

- Python 3.12+
- Docker
- Terraform 1.5+
- AWS CLI skonfigurowane z odpowiednimi uprawnieniami

## Uruchomienie lokalne

### Bez Dockera

```bash
cd app
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Z Dockerem

```bash
docker build -t book-search-api .
docker run -p 8000:8000 book-search-api
```

### Z docker-compose (z Nginx)

```bash
docker-compose up
```

Aplikacja dostępna pod: http://localhost (port 80, przez Nginx)  
Dokumentacja API (Swagger): http://localhost/docs

### Testy

```bash
pip install -r app/requirements-dev.txt
pytest app/test_main.py -v
```

## Wdrożenie na AWS

### 1. Infrastruktura (Terraform)

```bash
cd terraform

# Skopiuj i uzupełnij zmienne
cp terraform.tfvars.example terraform.tfvars
# Edytuj terraform.tfvars – uzupełnij ec2_key_pair_name

terraform init
terraform plan
terraform apply
```

Po zakończeniu Terraform wyświetli:
- `app_url` – publiczny adres aplikacji
- `ecr_repository_url` – adres repozytorium ECR

### 2. GitHub Secrets

W ustawieniach repozytorium GitHub dodaj następujące Secrets:

| Secret | Opis |
|--------|------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key ID |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key |
| `EC2_HOST` | Publiczny adres IP EC2 (z outputu Terraform) |
| `EC2_SSH_KEY` | Zawartość pliku `.pem` klucza EC2 |

### 3. Pierwsze wdrożenie

Po skonfigurowaniu secrets wykonaj push do brancha `main` – pipeline CI/CD automatycznie:
1. Uruchomi testy
2. Zbuduje obraz Docker
3. Wgra obraz do ECR
4. Zaloguje się na EC2 przez SSH i uruchomi nowy kontener

## CI/CD Pipeline

Pipeline (`.github/workflows/ci-cd.yml`) uruchamia się przy każdym push do `main`:

```
push → test → build Docker image → push to ECR → deploy to EC2
```

Przy pull requestach wykonywane są tylko testy (bez deployu).

## Struktura projektu

```
.
├── app/
│   ├── main.py              # Aplikacja FastAPI
│   ├── requirements.txt     # Zależności produkcyjne
│   ├── requirements-dev.txt # Zależności deweloperskie (testy)
│   └── test_main.py         # Testy pytest
├── nginx/
│   └── nginx.conf           # Konfiguracja Nginx (reverse proxy)
├── terraform/
│   ├── main.tf              # EC2, ECR, IAM, Security Group
│   ├── variables.tf         # Zmienne
│   ├── outputs.tf           # Outputy (IP, URL, ECR)
│   ├── userdata.sh          # Skrypt startowy EC2 (Docker, Compose, CloudWatch)
│   └── terraform.tfvars.example
├── .github/
│   └── workflows/
│       └── ci-cd.yml        # GitHub Actions pipeline
├── Dockerfile
├── docker-compose.yml       # Lokalny dev (build from source)
├── docker-compose.prod.yml  # Produkcja EC2 (obraz z ECR)
└── README.md
```

## Przykłady użycia

```bash
# Health check
curl http://<EC2_IP>/health

# Wersja
curl http://<EC2_IP>/version

# Wyszukiwanie książek
curl "http://<EC2_IP>/search?title=Wiedźmin&limit=3"
curl "http://<EC2_IP>/search?title=Clean+Code"
```

## Link do działającej aplikacji

> **TODO:** Po wdrożeniu uzupełnij tutaj publiczny adres URL.
