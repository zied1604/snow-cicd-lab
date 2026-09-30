## Contexte
Ticket : PROJ-XXX
Pourquoi ce changement ?
## Checklist
- [ ] Tests dbt ajoutes ou mis a jour (not_null, unique, relationships)
- [ ] Pas de select * ni de donnees en dur
- [ ] Modele documente dans schema.yml
- [ ] Impact sur les couts warehouse evalue
- [ ] Aucune donnee sensible ni secret dans le diff
- [ ] Plan de retour arriere (rollback) decrit si le changement est risque