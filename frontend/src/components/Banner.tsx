import { useEffect, useState } from "react";

interface Slide {
  title: string;
  heading: string;
  entries: { icon: string; title: string; text: string }[];
}

/** Contenido propio de HUARMY SGD. Describe objetivos del sistema, no funciones ya disponibles. */
const SLIDES: Slide[] = [
  {
    title: "OBJETIVOS DEL",
    heading: "SISTEMA DE GESTIÓN DOCUMENTAL",
    entries: [
      { icon: "🔎", title: "Consulta rápida", text: "Búsqueda por filtros." },
      { icon: "🌱", title: "Cero papel", text: "Cultura de ecoeficiencia." },
      { icon: "📍", title: "Seguimiento", text: "Estado y trazabilidad de los documentos." },
      { icon: "🔗", title: "Interoperabilidad", text: "Integración con otros sistemas del Estado." },
      { icon: "🔏", title: "Firmas digitales", text: "Con certificados de validez legal." },
      { icon: "⚡", title: "Acceso rápido", text: "Menos tiempo de atención." },
    ],
  },
  {
    title: "NIVELES DE",
    heading: "VISIBILIDAD DE DOCUMENTOS",
    entries: [
      { icon: "👤", title: "Acceso personal", text: "Documentos que usted genera o recibe." },
      { icon: "🏢", title: "Acceso total", text: "Documentos de toda su oficina, salvo confidenciales." },
      { icon: "🛡️", title: "Firma aparte", text: "El acceso total no permite firmar, aprobar, emitir ni anular." },
    ],
  },
];

export function Banner() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setIndex((i) => (i + 1) % SLIDES.length), 8000);
    return () => clearInterval(id);
  }, []);

  const slide = SLIDES[index];
  return (
    <section className="overflow-hidden rounded-lg shadow-sm" aria-label="Información del sistema">
      <div className="h-2 bg-gradient-to-r from-teal-600 via-emerald-600 via-60% to-amber-500" />
      <div className="relative bg-gradient-to-br from-brand-900 via-brand-800 to-emerald-900 px-5 py-8 sm:px-10">
        <p className="text-center text-xl font-extrabold tracking-wide text-white sm:text-3xl">{slide.title}</p>
        <p className="mx-auto mt-2 w-fit rounded-xl bg-teal-600 px-5 py-1.5 text-center text-lg font-extrabold text-white sm:text-2xl">
          {slide.heading}
        </p>

        <div className="mx-auto mt-6 grid max-w-3xl gap-4 rounded-2xl bg-white/95 p-5 sm:grid-cols-2">
          {slide.entries.map((e) => (
            <div key={e.title} className="flex items-start gap-3">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xl" aria-hidden="true">
                {e.icon}
              </span>
              <div>
                <p className="font-bold text-emerald-800">{e.title}</p>
                <p className="text-sm text-slate-600">{e.text}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-5 flex justify-center gap-2">
          {SLIDES.map((_, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setIndex(i)}
              aria-label={`Ver diapositiva ${i + 1}`}
              className={`h-2.5 w-2.5 rounded-full ${i === index ? "bg-white" : "bg-white/40"}`}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
