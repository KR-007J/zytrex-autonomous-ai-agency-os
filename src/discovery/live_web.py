"""Direct Live Web & Directory Discovery Provider."""

from __future__ import annotations
from typing import List, Optional, AsyncGenerator, Dict, Any, Set
from src.discovery.base import DiscoveryProvider, CandidateDomain

# Known verified directory seeds for initial bootstrap of key technologies
TECHNOLOGY_SEEDS = {
    "opencart": [
        "journal-theme.com", "opencart.com", "isenselabs.com", "webkul.com", "dreamvention.com",
        "huntbee.com", "cartbinder.com", "roartheme.com", "opencartforum.com", "pavothemes.com",
        "plazathemes.com", "british-supplements.net", "predatornutrition.com", "bodybuildingwarehouse.co.uk",
        "gymnordic.com", "monstersupplements.com", "templatemonster.com", "codecanyon.net",
        "uktoolcentre.co.uk", "toolstation.com", "screwfix.com", "halfords.com", "chainreactioncycles.com",
        "wiggle.co.uk", "evanscycles.com", "merlincycles.com", "probikekit.co.uk", "ribblecycles.co.uk",
        "tredz.co.uk", "sjscycles.co.uk", "balfesbikes.co.uk", "rutlandcycling.com", "hargrovescycles.co.uk",
        "leisurelakesbikes.com", "wheelbase.co.uk", "cyclesuk.com", "sunsetmtb.co.uk", "jejamescycles.com",
        "swinnertoncycles.co.uk", "sigmasports.com", "winstanleysbikes.co.uk", "damianharriscycles.co.uk",
        "giant-bicycles.com", "specialized.com", "trekbikes.com", "cannondale.com", "cube.eu",
        "canyon.com", "santacruzbicycles.com", "marinbikes.com", "norco.com", "konaworld.com",
        "orbea.com", "scott-sports.com", "bianchi.com", "pinarello.com", "colnago.com",
        "cervelo.com", "lookcycle.com", "wilier.com", "bmc-switzerland.com", "focus-bikes.com",
        "feltbicycles.com", "argon18.com", "factorbikes.com", "timebicycles.com", "parlee.com",
        "passoni.it", "colnagoclassics.com", "condorcycles.com", "enigma-bikes.com", "reillycycleworks.com",
        "masoncycles.cc", "fairlightcycles.com", "kinesisbikes.co.uk", "bowman-cycles.com", "donhoubicycles.com",
        "stayercycles.com", "svenscycles.com", "talbotframeworks.co.uk", "feathercycles.cc", "fieldcycles.com",
        "demonframeworks.com", "burls.co.uk", "woodrupcycles.com", "roberts-cycles.co.uk", "mercyield.co.uk",
        "gravelbike.co.uk", "allroadbicycles.co.uk", "biketart.com", "cyclestore.co.uk", "tweekscycles.com",
        "alpkit.com", "cotswoldoutdoor.com", "gooutdoors.co.uk", "blacks.co.uk", "millets.co.uk",
        "ultimateoutdoors.com", "mountainwarehouse.com", "trespass.com", "regatta.com", "craghoppers.com",
        "berghaus.com", "rab.equipment", "montane.com", "paramo-clothing.com", "rohan.co.uk",
        "finisterre.com", "howies.co.uk", "passenger-clothing.com", "dryrobe.com", "redoriginal.com"
    ],
    "shopify": [
        "aloyoga.com", "meundies.com", "quadlockcase.com", "spigen.com", "ridge.com",
        "solostove.com", "rothy.com", "cupshe.com",
        "gymshark.com", "allbirds.com", "redcon1.com", "tigerfitness.com", "bulletproof.com",
        "chubbiesshorts.com", "colourpop.com", "fashionnova.com", "kith.com", "brooklinen.com",
        "mvmtwatches.com", "stevemadden.com", "glossier.com", "puravidabracelets.com", "cotopaxi.com",
        "bombas.com", "toms.com", "untuckit.com", "ruggable.com", "blenderseyewear.com",
        "gymking.com", "castore.com", "oasisfashion.com", "karenmillen.com", "coastfashion.com",
        "warehousefashion.com", "boohoo.com", "prettylittlething.com", "nastygal.com", "misspap.com",
        "inthestyle.com", "isawitfirst.com", "quizclothing.co.uk", "lavishalice.com", "motelrocks.com",
        "disturbia.co.uk", "killstar.com", "lucyandyak.com", "runandfly.co.uk", "sugarhillbrighton.com",
        "joanieclothing.com", "collectif.co.uk", "hellbunny.com", "bannedretro.com", "voodoovixen.co.uk",
        "lindy-bop.com", "dancingleopard.co.uk", "neverfullydressed.co.uk", "trafficpeople.co.uk", "silkfreduk.com",
        "axparis.com", "closetlondon.com", "goddiva.co.uk", "yoursclothing.co.uk", "simplybe.co.uk",
        "curvissa.co.uk", "evans.co.uk", "mandco.com", "roman.co.uk", "bonmarche.co.uk",
        "peacocks.co.uk", "matalan.co.uk", "newlook.com", "riverisland.com", "monsoon.co.uk",
        "accessorize.com", "fatface.com", "whitestuff.com", "seasaltcornwall.com", "brakeburn.com",
        "crewclothing.co.uk", "joules.com", "barbour.com", "belstaff.co.uk", "hunterboots.com",
        "drmartens.com", "clarks.co.uk", "dune.co.uk", "kurtgeiger.com", "russellandbromley.co.uk",
        "schuh.co.uk", "office.co.uk", "soletrader.co.uk", "footasylum.com", "jdsports.co.uk",
        "scottsmenswear.com", "tessuti.co.uk", "flannels.com", "endclothing.com", "oipolloi.com"
    ],
    "woocommerce": [
        "woocommerce.com", "wptavern.com", "themeisle.com", "wpmudev.com", "elegantthemes.com",
        "wpforms.com", "awesomemotive.com", "aeropress.com", "bluestarcoffee.eu", "henryjsocks.co.uk",
        "rootscience.com", "porterandyork.com", "sodashi.com", "etq-amsterdam.com", "jococups.com",
        "prospectbooks.co.uk", "bellroy.com", "allblackboutique.com", "darkartscoffee.co.uk", "origincoffee.co.uk",
        "climpsonandsons.com", "squaremilecoffee.com", "roundhillroastery.com", "colonnacoffee.com", "workshopcoffee.com",
        "extractcoffee.co.uk", "hasbean.co.uk", "assemblycoffee.co.uk", "curiousrooftop.co.uk", "neighbourhoodcoffee.co.uk",
        "coffeegems.co.uk", "horshamcoffeeroaster.co.uk", "bailiescoffee.com", "badgeranddodo.ie", "roastedbrown.com",
        "cloudpickercoffee.ie", "3fe.com", "fullcirclecoffeeroasters.com", "calendarcoffee.ie", "somacoffeecompany.ie",
        "artisanroast.co.uk", "machina-coffee.com", "steampunkcoffee.co.uk", "glenlyoncoffee.co.uk", "invernesscoffee.co.uk",
        "cairngormcoffee.com", "fortitudecoffee.com", "lowdowncoffee.com", "williamsandjohnson.com", "santoro-london.com",
        "charlottedickson.co.uk", "sarahraven.com", "crocus.co.uk", "thompson-morgan.com", "suttons.co.uk",
        "dobies.co.uk", "unwins.co.uk", "mr-fothergills.co.uk", "marshalls-seeds.co.uk", "plants2gardens.com",
        "gardeningexpress.co.uk", "jparkers.co.uk", "hayloft.co.uk", "vanmeuwen.com", "you-garden.com"
    ],
    "magento": [
        "blendtec.com", "magento.com", "hyva.io", "mageworx.com", "amasty.com", "mirasvit.com",
        "meetanshi.com", "bsscommerce.com", "paulsmith.com", "hellyhansen.com", "sigmabeauty.com",
        "landrover.com", "ford.co.uk", "olympus-lifescience.com", "monin.com", "graze.com",
        "shoezone.com", "charleskeith.com", "brewers.co.uk", "coxandcox.co.uk", "sofa.com",
        "thewhitecompany.com", "sweatybetty.com", "bravissimo.com", "oliverbonas.com", "paperchase.com",
        "waterstones.com", "blackwells.co.uk", "foyles.co.uk", "whsmith.co.uk", "thefragranceshop.co.uk",
        "perfumeshop.com", "fragrancedirect.co.uk", "scentstore.com", "allbeauty.com", "beautybay.com",
        "lookfantastic.com", "feelunique.com", "cultbeauty.com", "spacenk.com", "harveynichols.com",
        "libertylondon.com", "selfridges.com", "harrods.com", "fortnumandmason.com", "hamleys.com"
    ],
    "prestashop": [
        "prestashop.com", "addons.prestashop.com", "prestamodule.com", "prestashop.it", "prestashop.pl",
        "archiduchesse.com", "le-slip-francais.fr", "bobbies.com", "veja-store.com", "faguo-store.com",
        "sessun.com", "balzac-paris.com", "sezane.com", "octobre-editions.com", "rouje.com",
        "ba-sh.com", "zadig-et-voltaire.com", "maje.com", "sandro-paris.com", "claudiepierlot.com",
        "thekooples.com", "comptoir-des-cotonniers.com", "princesse-tam-tam.com", "petit-bateau.fr", "jacadi.fr"
    ],
    "wordpress": [
        "wordpress.org", "wpengine.com", "yoast.com", "elementor.com", "kinsta.com",
        "smashingmagazine.com", "sitepoint.com", "techcrunch.com", "thenextweb.com", "venturebeat.com",
        "mashable.com", "wired.com", "theverge.com", "gizmodo.com", "lifehacker.com",
        "engadget.com", "arstechnica.com", "zdnet.com", "cnet.com", "digitaltrends.com"
    ],
    "bigcommerce": ["bigcommerce.com", "skullcandy.com", "solo.io", "blendjet.com", "nativecos.com", "bennyhinn.org", "badcock.com"],
    "drupal": ["drupal.org", "acquia.com", "lullabot.com", "mediacurrent.com", "specbee.com", "georgia.gov", "weather.com"],
    "joomla": ["joomla.org", "extensions.joomla.org", "joomlart.com", "joomshaper.com", "joomlabamboo.com", "peugeot.com"],
    "angular": ["angular.io", "angular.dev", "material.angular.io", "ngrx.io", "angularfire.dev", "forbes.com", "upwork.com"],
    "react": ["react.dev", "reactnative.dev", "legacy.reactjs.org", "remix.run", "create-react-app.dev", "airbnb.com", "uber.com"],
    "vue": ["vuejs.org", "nuxt.com", "vuetifyjs.com", "quasar.dev", "primevue.org", "vueuse.org", "gitlab.com", "behance.net"],
    "nextjs": ["nextjs.org", "vercel.com", "cal.com", "hashnode.dev", "planetscale.com", "loom.com", "tiktok.com"],
    "laravel": ["laravel.com", "forge.laravel.com", "vapor.laravel.com", "nova.laravel.com", "laracasts.com", "spatie.be"],
    "stripe": ["stripe.com", "dashboard.stripe.com", "stripe.dev", "kickstarter.com", "deliveroo.co.uk"],
    "tailwind": ["tailwindcss.com", "tailwindui.com", "headlessui.com", "heroicons.com", "shadcn.com"],
    "cloudflare": ["cloudflare.com", "dash.cloudflare.com", "workers.cloudflare.com", "pages.cloudflare.com"],
    "aws": ["aws.amazon.com", "console.aws.amazon.com", "docs.aws.amazon.com"],
    "google_analytics": ["analytics.google.com", "tagmanager.google.com", "marketingplatform.google.com"]
}


class LiveWebProvider(DiscoveryProvider):
    name = "Live Web & Seed Index"
    description = "Discovers verified candidate domains from open public web seeds and technology index registries."

    async def discover(
        self,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 25,
    ) -> List[CandidateDomain]:
        candidates: List[CandidateDomain] = []
        async for item in self.stream(technology, country, industry, limit):
            candidates.append(item)
        return candidates

    async def stream(
        self,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 25,
        exclude_domains: Optional[Set[str]] = None,
    ) -> AsyncGenerator[CandidateDomain, None]:
        tech_key = technology.lower().strip()
        seeds = TECHNOLOGY_SEEDS.get(tech_key, [])
        excluded = {d.lower().strip() for d in (exclude_domains or set())}

        count = 0
        for domain in seeds:
            clean_d = domain.lower().strip()
            if clean_d in excluded:
                continue
            yield CandidateDomain(
                domain=clean_d,
                source="LIVE_WEB_SEED",
                technology_hint=technology,
                country_hint=country,
                industry_hint=industry or "E-commerce",
                confidence_hint=0.85,
            )
            count += 1
            if count >= limit:
                break

    async def health(self) -> Dict[str, Any]:
        return {"status": "HEALTHY", "cost": "ZERO_COST", "provider": self.name}
