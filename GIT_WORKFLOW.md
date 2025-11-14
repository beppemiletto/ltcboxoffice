# Git Workflow - LTC Box Office

## Strategia di Branching

Il progetto utilizza una strategia di branching semplificata per garantire stabilità in produzione.

### Branch Principali

#### `production` (principale)
- **Scopo**: Codice stabile pronto per il deployment
- **Protezione**: Solo merge da feature branch testati
- **Deploy**: Automatico o manuale verso server produzione
- **Stato attuale**: Cookie consent system (commit 81e7055)

#### `feature/*` (temporanei)
- **Scopo**: Sviluppo di nuove funzionalità
- **Workflow**: Creato da production, mergiato dopo testing
- **Naming**: `feature/nome-funzionalità`
- **Esempio**: `feature/venue-management` (in sviluppo)

---

## Branch Attivi

### 🚀 production (STABLE)
```
HEAD: 81e7055 - feat: Implement GDPR-compliant cookie consent system
Status: Ahead of origin/production by 2 commits
Ready for push: YES
```

**Recent commits:**
- 81e7055: GDPR cookie consent system
- d878d6e: Regex warnings fix
- bc408ed: Windows dependencies compatibility
- 72be7e5: Professional Django standards upgrade

### 🔬 feature/venue-management (TESTING)
```
HEAD: b85198a - docs: Add comprehensive testing checklist
Branch from: production (81e7055)
Status: In development, needs testing
Ready for merge: NO (see TESTING_VENUE_MANAGEMENT.md)
```

**Commits in this feature:**
- b85198a: Testing checklist
- c02d5ec: Multi-venue management system

**Changes:**
- Multi-venue support with JSON/XML configs
- Management commands: load_venue_config, export_venue_config  
- Database migrations: billboard.0016, hall.0004
- 263 seats imported for Teatro Cambiano
- Documentation: VENUE_MANAGEMENT.md

---

## Workflow Standard

### 1. Creare Nuova Feature

```bash
# Assicurati di essere su production aggiornato
git checkout production
git pull origin production

# Crea feature branch
git checkout -b feature/nome-funzionalita

# Lavora sulla feature
# ... sviluppo ...

# Commit incrementali
git add -A
git commit -m "tipo: descrizione breve"
```

### 2. Testing della Feature

```bash
# Mentre sei su feature branch
python manage.py check
python manage.py test

# Vedi checklist specifica feature (es. TESTING_VENUE_MANAGEMENT.md)
```

### 3. Merge in Production

```bash
# Solo dopo testing completo!
git checkout production
git merge feature/nome-funzionalita

# Risolvi eventuali conflitti
# Test finale
python manage.py check
python manage.py migrate --plan

# Push
git push origin production
```

### 4. Cleanup

```bash
# Dopo merge riuscito
git branch -d feature/nome-funzionalita

# Se feature non più necessaria
git branch -D feature/nome-funzionalita
```

---

## Convenzioni Commit

### Formato
```
<tipo>: <descrizione breve>

[corpo opzionale con dettagli]

[footer opzionale con breaking changes]
```

### Tipi Commit
- `feat`: Nuova funzionalità
- `fix`: Bug fix
- `docs`: Solo documentazione
- `refactor`: Refactoring (no feature/fix)
- `test`: Aggiunta/modifica test
- `chore`: Manutenzione (deps, config)
- `perf`: Miglioramento performance
- `style`: Formattazione codice

### Esempi
```bash
git commit -m "feat: add venue management system with JSON import"

git commit -m "fix: resolve cookie consent redirect loop"

git commit -m "docs: update QUICKSTART.md with venue instructions"

git commit -m "refactor: extract venue loading into separate service"
```

---

## Stato Corrente Progetto

### Production Branch (pronto per push)
✅ Professional Django structure  
✅ Windows-compatible dependencies  
✅ Regex warnings fixed  
✅ GDPR cookie consent system  
⏳ Venue management (in feature branch)

### Feature Branches in Sviluppo

#### feature/venue-management
**Status**: 🔬 Testing in progress  
**Progress**: 40% (vedere TESTING_VENUE_MANAGEMENT.md)  
**Blockers**: 
- [ ] Integration with hall/views.py
- [ ] Multi-venue testing
- [ ] Performance benchmarks

**ETA merge**: Dopo completamento testing checklist

---

## Prossimi Passi

### Immediati (Production)
1. Push commits cookie consent a origin:
   ```bash
   git checkout production
   git push origin production
   ```

2. Tag release:
   ```bash
   git tag -a v2.0.0 -m "Professional upgrade + Cookie consent"
   git push origin v2.0.0
   ```

### Feature Branch (venue-management)
1. Completare testing checklist (TESTING_VENUE_MANAGEMENT.md)
2. Aggiornare hall/views.py per multi-venue
3. Testare con venue multipli
4. Code review
5. Merge in production quando stabile

### Futuri Feature Branch
- `feature/redis-caching`: Cache sistema prenotazioni
- `feature/email-notifications`: Sistema notifiche email
- `feature/reporting`: Dashboard statistiche
- `feature/api-rest`: API REST per mobile app

---

## Rollback Strategy

### Se problemi dopo merge in production

```bash
# Identifica commit problematico
git log --oneline -10

# Revert commit specifico
git revert <commit-hash>

# Oppure reset hard (PERICOLOSO - solo se no push)
git reset --hard <commit-precedente>

# Rollback database
python manage.py migrate app_name <migration_number>
```

### Esempio: Rollback venue-management
```bash
git checkout production
git revert c02d5ec  # Revert venue management commit
python manage.py migrate billboard 0015
python manage.py migrate hall 0003
```

---

## Best Practices

### ✅ DO
- Testa sempre su feature branch prima di merge
- Usa `--dry-run` per operazioni database critiche
- Commit piccoli e frequenti con messaggi chiari
- Mantieni production sempre deployable
- Crea backup database prima di migrations grandi
- Usa checklist testing per feature complesse

### ❌ DON'T
- Non committare direttamente su production (usa feature branch)
- Non fare push force su production (`git push -f`)
- Non committare file sensibili (.env, secrets)
- Non mergiare feature non testate
- Non fare migrations senza backup

---

## Git Aliases Utili

Aggiungi a `.git/config` o `~/.gitconfig`:

```ini
[alias]
    st = status
    co = checkout
    br = branch -v
    ci = commit
    lg = log --oneline --graph --decorate --all -20
    last = log -1 HEAD
    unstage = reset HEAD --
    feature = checkout -b feature/
    done = !git checkout production && git merge @{-1}
```

Uso:
```bash
git feature venue-import  # Crea feature/venue-import
git done                   # Merge current feature in production
```

---

## Contatti & Support

**Maintainer**: Beppe Miletto (@beppemiletto)  
**Repository**: ltcboxoffice  
**CI/CD**: GitHub Actions (vedere .github/workflows/ci.yml)

Per domande sul workflow Git:
- Consulta questa guida
- Vedi documentazione GitHub del progetto
- Contatta team lead prima di operazioni rischiose

---

**Ultimo aggiornamento**: 2025-11-14  
**Versione documento**: 1.0
