# Book Search API

Prosta aplikacja REST API do wyszukiwania książek po tytule, korzystająca z [OpenLibrary.org](https://openlibrary.org).
do pokazania budowani i wdrażania aplikacji na AWSie

## Opis projektu

API udostępnia trzy endpointy:
- `GET /health` – sprawdzenie stanu aplikacji
- `GET /version` – zwraca wersję aplikacji
- `GET /search?title=<tytuł>&limit=<n>` – wyszukuje książki w OpenLibrary.org

## Architektura v4.1

```
GitHub → GitHub Actions → Amazon ECR → Amazon ECS (t3.micro, Amazon Linux 2023)
                                              ↓
                                     Nginx (port 80)
                                              ↓
                                    FastAPI app (port 8000)
                                              ↓
                                     CloudWatch Logs
```
Infrastruktura składa się z:
- **Amazon ECR** – rejestr obrazów Docker
- **Amazon ECS** – klaster i serwis zarządzający kontenerem aplikacji
- **Amazon EC2** – instancja t3.micro z ECS-optimized AMI
- **CloudWatch** – logi aplikacji w grupie `/ecs/wyszukiwarka-ksiazek`

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
# Edytuj terraform.tfvars – uzupełnij ec2_key_pair_name

terraform init
terraform plan -var="ec2_key_pair_name=<nazwa_klucza>"
terraform apply -var="ec2_key_pair_name=<nazwa_klucza>"
```

Po zakończeniu Terraform wyświetli:
- `app_url` – publiczny adres aplikacji
- `ecr_repository_url` – adres repozytorium ECR
- `ecs_cluster_name` – nazwa klastra ECS
- `ecs_service_name` – nazwa serwisu ECS


### 2. GitHub Secrets

W ustawieniach repozytorium GitHub dodaj następujące Secrets:

| Secret | Opis |
|--------|------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key ID użytkownika IAM |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key użytkownika IAM |
| `EC2_KEY_PAIR_NAME` | Nazwa klucza EC2 w AWS (np. `book-search-key`) |

### 3. Pierwsze wdrożenie

1. Zastosuje konfigurację Terraform (infrastruktura)
2. Uruchomi testy jednostkowe
3. Zbuduje obraz Docker z numerem wersji
4. Wgra obraz do ECR
5. Po ręcznej akceptacji środowiska `production` – wdrożenie na ECS

## CI/CD Pipeline

Pipeline (`.github/workflows/ci-cd.yml`) uruchamia się przy każdym push do `main`:

```
terraform → test → build & push → (akceptacja) → deploy to ECS
```

Przy pull requestach wykonywane są tylko testy (bez deployu).

Wersja aplikacji jest automatycznie generowana jako `1.0.<numer_runu>` i wbudowywana w obraz Docker.

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
│   └── terraform.tfvars     # zmienne region aws, klucze, dostęp siec
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
lub poprzez stronę http://<EC2_IP>
```

## Link do działającej aplikacji
nowy adres
