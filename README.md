# Reasis - Plataforma de Actividades de Aprendizaje

## Acerca de este proyecto

**Reasis** es una plataforma educativa digital diseñada para el desarrollo y gestión de actividades de aprendizaje para estudiantes de la red "Fe y Alegría". El objetivo principal es crear un ecosistema digital que facilite el aprendizaje activo, personalizado e interactivo para los estudiantes.

## Nuevo Enfoque del Proyecto (2025)

Tras la exitosa finalización del proyecto de consultoría de clustering de instituciones educativas, **Reasis** se transforma para enfocarse en:

### 🎯 Objetivo Principal
Desarrollar una plataforma integral para la creación, gestión y seguimiento de actividades de aprendizaje que permita:
- **Aprendizaje Personalizado**: Adaptación de contenidos según el perfil del estudiante
- **Engagement Educativo**: Actividades interactivas y gamificadas
- **Seguimiento de Progreso**: Métricas de aprendizaje en tiempo real
- **Colaboración**: Herramientas para trabajo en equipo y proyectos colaborativos

### 🎓 Público Objetivo
- **Estudiantes**: Usuarios principales de la plataforma
- **Docentes**: Creadores y facilitadores de actividades
- **Coordinadores Académicos**: Supervisión y análisis de progreso
- **Administradores**: Gestión de la plataforma

## Características Principales

### Para Estudiantes
- 📚 **Biblioteca de Actividades**: Acceso a diversas actividades educativas organizadas por materia y nivel
- 🎮 **Gamificación**: Sistema de puntos, insignias y logros para motivar el aprendizaje
- 📊 **Dashboard Personal**: Seguimiento de progreso individual y metas de aprendizaje
- 👥 **Colaboración**: Herramientas para trabajar en equipos y proyectos grupales
- 📱 **Accesibilidad**: Diseño responsive para dispositivos móviles y computadoras

### Para Docentes
- ✏️ **Creador de Actividades**: Herramientas intuitivas para diseñar actividades interactivas
- 📈 **Analytics de Aprendizaje**: Métricas detalladas del progreso estudiantil
- 🎯 **Personalización**: Capacidad de adaptar actividades según necesidades específicas
- 📋 **Gestión de Grupos**: Organización y seguimiento de clases y grupos de trabajo
- 💬 **Retroalimentación**: Sistema de comunicación bidireccional con estudiantes

### Para Administradores
- 🏫 **Gestión Institucional**: Administración de múltiples instituciones de la red
- 📊 **Reportes Centralizados**: Dashboard ejecutivo con métricas consolidadas
- 👤 **Gestión de Usuarios**: Control de accesos y permisos
- 🔧 **Configuración**: Personalización de la plataforma por institución

## Stack Tecnológico

### Frontend
- **Framework**: Flutter (Multiplataforma)
- **Herramientas**: FlutterFlow para desarrollo visual
- **UI/UX**: Material Design 3
- **Estado**: Bloc/Cubit para gestión de estado

### Backend
- **Plataforma**: Supabase
- **Base de Datos**: PostgreSQL
- **Autenticación**: Supabase Auth
- **API**: REST API con Supabase
- **Storage**: Supabase Storage para archivos multimedia

### Infraestructura
- **Hosting**: Supabase Cloud
- **CDN**: Integrado con Supabase
- **Monitoring**: Supabase Analytics
- **Backup**: Automated backups de Supabase

## Estructura del Proyecto

```
Reasis/
├── archivado/
│   └── clustering/              # Proyecto anterior archivado
├── lib/                         # Código Flutter principal
│   ├── core/                    # Funcionalidades base
│   ├── features/                # Módulos por funcionalidad
│   │   ├── auth/               # Autenticación y autorización
│   │   ├── activities/         # Gestión de actividades
│   │   ├── students/           # Perfil y progreso estudiantil
│   │   ├── teachers/           # Herramientas para docentes
│   │   └── admin/              # Panel administrativo
│   ├── shared/                 # Componentes compartidos
│   └── main.dart               # Punto de entrada
├── assets/                     # Recursos estáticos
│   ├── images/
│   ├── icons/
│   └── fonts/
├── docs/                       # Documentación del proyecto
├── test/                       # Pruebas unitarias e integración
└── supabase/                   # Configuración de backend
    ├── migrations/             # Migraciones de base de datos
    └── functions/              # Funciones edge
```

## Módulos Principales

### 1. 🔐 Autenticación y Perfiles
- Login/registro por roles (estudiante, docente, admin)
- Perfiles personalizables
- Gestión de permisos

### 2. 📚 Gestión de Actividades
- Creador visual de actividades
- Biblioteca categorizada
- Sistema de etiquetas y filtros
- Versionado de actividades

### 3. 🎓 Experiencia Estudiantil
- Dashboard personalizado
- Progreso gamificado
- Colaboración en tiempo real
- Portfolio digital

### 4. 👨‍🏫 Herramientas Docentes
- Analytics de aprendizaje
- Seguimiento individualizado
- Comunicación con estudiantes
- Planificación curricular

### 5. 📊 Administración
- Métricas institucionales
- Gestión de usuarios
- Configuración de plataforma
- Reportes ejecutivos

## Metodología de Desarrollo

- **Agile/Scrum**: Sprints de 2 semanas
- **Design Thinking**: Centrado en la experiencia del usuario
- **Testing**: TDD con cobertura mínima del 80%
- **CI/CD**: Integración y despliegue continuo
- **Documentación**: Docs as Code

## Estado Actual

🚀 **PROYECTO EN INICIO**  
📅 **Fecha de Inicio**: Enero 2025  
🎯 **Fase Actual**: Planificación y diseño arquitectónico

## Próximos Pasos

1. **Diseño UX/UI**: Wireframes y prototipos de alta fidelidad
2. **Arquitectura Backend**: Diseño de base de datos y APIs
3. **MVP**: Desarrollo de funcionalidades básicas
4. **Testing**: Pruebas con usuarios piloto
5. **Lanzamiento**: Despliegue progresivo en instituciones Fe y Alegría

## Contacto y Colaboración

Este proyecto es desarrollado para la red educativa "Fe y Alegría" con el objetivo de transformar la experiencia de aprendizaje de los estudiantes mediante tecnología educativa innovadora.

---

**Desarrollado con ❤️ para la educación**
