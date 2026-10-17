// @ts-check
import starlight from "@astrojs/starlight";
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://naija-data.asgatcreation.workers.dev",
  integrations: [
    starlight({
      title: "naija-data",
      logo: { src: "./src/assets/logo.svg" },
      customCss: ["./src/styles/custom.css"],
      head: [
        { tag: "meta", attrs: { property: "og:image", content: "https://naija-data.asgatcreation.workers.dev/social-preview.png" } },
        { tag: "meta", attrs: { property: "og:image:width", content: "1280" } },
        { tag: "meta", attrs: { property: "og:image:height", content: "640" } },
        { tag: "meta", attrs: { name: "twitter:card", content: "summary_large_image" } },
        { tag: "meta", attrs: { name: "twitter:image", content: "https://naija-data.asgatcreation.workers.dev/social-preview.png" } },
      ],
      description: "Accurate, sourced Nigerian reference data for Python, JavaScript/TypeScript and Go, plus a free REST API.",
      social: [{ icon: "github", label: "GitHub", href: "https://github.com/asgatcreation/naija-data" }],
      editLink: { baseUrl: "https://github.com/asgatcreation/naija-data/edit/main/docs/site/" },
      lastUpdated: false,
      sidebar: [
        { label: "Playground", link: "/playground/" },
        {
          label: "Getting started",
          items: [
            { label: "Python", link: "/getting-started/python/" },
            { label: "JavaScript / TypeScript", link: "/getting-started/javascript/" },
            { label: "Go", link: "/getting-started/go/" },
            { label: "Django and DRF", link: "/getting-started/django/" },
            { label: "REST API", link: "/getting-started/api/" },
          ],
        },
        {
          label: "Guides",
          items: [
            { label: "State → LGA → ward dropdowns", link: "/guides/state-lga-form/" },
            { label: "Phone number fields", link: "/guides/phone-numbers/" },
            { label: "Bank account forms (NUBAN)", link: "/guides/bank-accounts/" },
            { label: "Account names (name enquiry)", link: "/guides/account-names/" },
            { label: "Senate, Reps and Assembly", link: "/guides/elections/" },
            { label: "Search and autocomplete", link: "/guides/search/" },
            { label: "Vehicle plates", link: "/guides/vehicle-plates/" },
            { label: "Use the data files (any language)", link: "/guides/raw-data/" },
          ],
        },
        {
          label: "Reference",
          items: [
            { label: "Functions (all languages)", link: "/reference/functions/" },
            { label: "REST API endpoints", link: "/reference/api/" },
          ],
        },
        {
          label: "Data",
          items: [
            { label: "Sources and methodology", link: "/data/sources/" },
            { label: "Coverage and known gaps", link: "/data/coverage/" },
            { label: "Contributing a correction", link: "/data/contributing/" },
          ],
        },
        { label: "Changelog", link: "/changelog/" },
      ],
    }),
  ],
});
