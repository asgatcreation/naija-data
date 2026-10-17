// @ts-check
import starlight from "@astrojs/starlight";
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://naija-data.asgatcreation.workers.dev",
  integrations: [
    starlight({
      title: "naija-data",
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
            { label: "Account names (name enquiry)", link: "/getting-started/account-names/" },
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
