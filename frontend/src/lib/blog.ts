export type BlogPostSummary = {
  slug: string;
  title: string;
  excerpt: string;
  category: string;
  image: string;
  imageAlt: string;
  readTime: string;
  featured?: boolean;
};

export type BlogArticleSection = {
  heading: string;
  paragraphs: string[];
  bullets?: string[];
};

export type BlogArticleContent = {
  introduction: string;
  sections: BlogArticleSection[];
  closing: string;
};

export const blogPosts: BlogPostSummary[] = [
  {
    slug: "build-a-simple-skincare-routine",
    title: "How to Build a Simple Skincare Routine",
    excerpt:
      "A practical guide to cleansing, moisturizing, sun protection, and introducing new products without overwhelming your skin.",
    category: "Skincare",
    image: "/images/face_cream.jpeg",
    imageAlt: "Face cream and skincare products arranged on a light surface",
    readTime: "5 min read",
    featured: true,
  },
  {
    slug: "prepare-your-skin-for-a-facial",
    title: "Preparing Your Skin for a Professional Facial",
    excerpt:
      "Learn what to share during consultation, what to avoid immediately before your appointment, and how to plan gentle aftercare.",
    category: "Clinical Aesthetics",
    image: "/images/facial_treatment.jpeg",
    imageAlt: "A client receiving a professional facial treatment",
    readTime: "4 min read",
  },
  {
    slug: "healthy-looking-hair-between-appointments",
    title: "Caring for Your Hair Between Salon Appointments",
    excerpt:
      "Simple habits for handling, moisture, heat, and product use that can support manageable, healthy-looking hair.",
    category: "Hair Care",
    image: "/images/hair_treatment.jpeg",
    imageAlt: "A professional hair-care treatment at a salon basin",
    readTime: "5 min read",
  },
  {
    slug: "bridal-beauty-preparation-timeline",
    title: "A Calm Bridal Beauty Preparation Timeline",
    excerpt:
      "A planning framework for consultations, skin and hair preparation, trials, and final appointments before your celebration.",
    category: "Bridal & Glam",
    image: "/images/bridal.jpeg",
    imageAlt: "Detailed bridal styling and traditional attire",
    readTime: "6 min read",
  },
  {
    slug: "face-oils-serums-and-creams",
    title: "Face Oils, Serums, and Creams: What Is the Difference?",
    excerpt:
      "Understand the general role of each product type and why texture, ingredients, and your individual skin needs matter.",
    category: "Product Guide",
    image: "/images/syrum_n_oil.jpeg",
    imageAlt: "Face serum, oil, and cream products",
    readTime: "5 min read",
  },
  {
    slug: "when-to-seek-professional-skin-advice",
    title: "When to Pause Products and Seek Professional Advice",
    excerpt:
      "Recognize persistent irritation, unexpected reactions, and other signs that call for stopping a routine and asking a qualified professional.",
    category: "Skin Safety",
    image: "/images/acne.jpeg",
    imageAlt: "A professional carrying out a facial skin-care treatment",
    readTime: "4 min read",
  },
];

export const blogArticleContent: Record<string, BlogArticleContent> = {
  "build-a-simple-skincare-routine": {
    introduction:
      "A useful skincare routine does not need many steps. Consistency, suitable products, and attention to how your skin responds are more important than following every trend.",
    sections: [
      {
        heading: "Begin with the essentials",
        paragraphs: [
          "Start with a gentle cleanser, a moisturizer, and daytime sun protection. These basic steps support cleanliness, comfort, and protection without making it difficult to identify which product is helping or causing irritation.",
          "Choose textures that feel comfortable on your skin. A product that is difficult or unpleasant to use regularly is unlikely to become part of a consistent routine.",
        ],
        bullets: [
          "Cleanse without aggressive scrubbing.",
          "Moisturize while the skin still feels slightly damp.",
          "Use suitable broad-spectrum sun protection during the day.",
        ],
      },
      {
        heading: "Introduce one change at a time",
        paragraphs: [
          "Adding several new products together makes reactions difficult to trace. Introduce one product, follow its instructions, and allow time to observe dryness, stinging, redness, breakouts, or other changes.",
          "Patch testing can reduce risk but cannot guarantee that a product will suit your entire face. Stop using a product if you experience a concerning reaction.",
        ],
      },
      {
        heading: "Build around your actual needs",
        paragraphs: [
          "Oiliness, dryness, sensitivity, pigmentation, and active skin conditions may require different approaches. Avoid assuming that a popular routine is automatically appropriate for you.",
          "Persistent or severe concerns deserve assessment by an appropriately qualified professional. Cosmetic information online should not replace medical diagnosis or treatment.",
        ],
      },
    ],
    closing:
      "Keep the routine simple enough to follow, observe your skin carefully, and seek individualized guidance before adding strong or specialized treatments.",
  },
  "prepare-your-skin-for-a-facial": {
    introduction:
      "Good facial preparation helps your provider understand your skin and reduces avoidable irritation. The most useful preparation is accurate information, not an aggressive last-minute routine.",
    sections: [
      {
        heading: "Share relevant information",
        paragraphs: [
          "Tell your provider about allergies, pregnancy, medication, current irritation, recent procedures, previous reactions, and prescription or strong skincare products. Bring product names or photographs if you are unsure of the ingredients.",
          "Be honest about discomfort and expectations. A responsible consultation may result in changing or postponing a treatment.",
        ],
      },
      {
        heading: "Keep the days before your visit gentle",
        paragraphs: [
          "Avoid experimenting with unfamiliar products immediately before an appointment. Excessive exfoliation, picking, squeezing, or scrubbing can leave skin more reactive.",
          "Follow any specific preparation instructions supplied by the branch. If your skin becomes irritated, sunburned, injured, or unwell before the appointment, contact the branch for guidance.",
        ],
      },
      {
        heading: "Plan for simple aftercare",
        paragraphs: [
          "Ask what sensations and appearance are normally expected after the selected facial and which products should be avoided. Protect treated skin from unnecessary friction and follow the aftercare instructions provided.",
          "Contact the provider promptly if you develop an unexpected or worsening reaction. Seek medical help when symptoms are severe or urgent.",
        ],
      },
    ],
    closing:
      "Preparation should protect your comfort and help the provider make an informed treatment decision—not force your skin to look perfect before you arrive.",
  },
  "healthy-looking-hair-between-appointments": {
    introduction:
      "Between salon visits, small handling and moisture habits can make hair easier to manage. Your ideal routine depends on hair type, styling, scalp condition, and chemical or heat history.",
    sections: [
      {
        heading: "Handle hair with patience",
        paragraphs: [
          "Detangle carefully using an approach suited to your hair and style. Work in manageable sections and avoid pulling through resistance, especially when hair is wet or already fragile.",
          "Protective styling should still feel comfortable. Pain, persistent tension, bumps, or scalp injury are signs to reassess the style.",
        ],
      },
      {
        heading: "Balance cleansing and moisture",
        paragraphs: [
          "Cleanse the scalp and hair often enough for your needs, then use suitable conditioning and moisturizing products. Heavy product buildup is not the same as healthy moisture.",
          "Apply products in sensible amounts and pay attention to how the scalp responds. Persistent itching, scaling, sores, or hair loss should be assessed appropriately.",
        ],
      },
      {
        heading: "Be thoughtful with heat and chemicals",
        paragraphs: [
          "Repeated high heat and overlapping chemical services can increase dryness and breakage. Use appropriate heat protection and avoid rushing from one major process into another without professional guidance.",
          "Tell your stylist about previous relaxers, color, treatments, reactions, and breakage so the service can be planned more safely.",
        ],
      },
    ],
    closing:
      "A consistent, gentle routine and honest communication with your stylist can support hair that looks and feels more manageable between visits.",
  },
  "bridal-beauty-preparation-timeline": {
    introduction:
      "Bridal beauty preparation is easier when decisions are spaced out. A calm timeline creates room for consultation, trials, adjustments, and realistic scheduling.",
    sections: [
      {
        heading: "Start with the overall plan",
        paragraphs: [
          "Discuss the event date, location, ceremony schedule, desired look, attire, headpiece or gele, hair requirements, and the number of people needing services. Share reference images as inspiration rather than guarantees.",
          "Confirm which services happen at a branch and whether any approved on-location arrangement affects timing, travel, or pricing.",
        ],
      },
      {
        heading: "Use trials to make decisions",
        paragraphs: [
          "Where a trial is available, use it to discuss comfort, color, finish, photography, wear time, and how the look works with attire and accessories.",
          "Record agreed products and styling details. Report sensitivities or reactions immediately instead of waiting until the event day.",
        ],
      },
      {
        heading: "Protect the final week",
        paragraphs: [
          "Avoid sudden, aggressive beauty experiments close to the ceremony. Confirm the appointment schedule, arrival time, branch or location, outstanding information, and payment requirements in advance.",
          "Prepare accessories and clothing so beauty services can proceed without unnecessary delays. Allow realistic time rather than building a schedule with no room for adjustment.",
        ],
      },
    ],
    closing:
      "The best timeline is the one agreed with your chosen professionals and adjusted to your own skin, hair, ceremony, and comfort.",
  },
  "face-oils-serums-and-creams": {
    introduction:
      "Oils, serums, and creams describe broad product formats, not guaranteed results. Understanding their general roles can help you ask better questions and avoid layering products simply because they are popular.",
    sections: [
      {
        heading: "Serums deliver concentrated formulas",
        paragraphs: [
          "Serums are often lightweight products designed around particular ingredients or concerns. Their strength and purpose vary widely, so read directions and avoid combining active ingredients without understanding how they interact.",
          "More serum is not necessarily better. Start cautiously and monitor your skin.",
        ],
      },
      {
        heading: "Creams support moisture and comfort",
        paragraphs: [
          "Creams commonly combine water, oils, and ingredients that help soften the skin and reduce moisture loss. Lighter or richer textures may suit different skin types, climates, and routines.",
          "A cream can support the skin barrier, but cosmetic moisturizers do not diagnose or cure medical skin conditions.",
        ],
      },
      {
        heading: "Oils help reduce moisture loss",
        paragraphs: [
          "Face oils can add softness and help seal in moisture, but they do not replace every step for every person. Some people prefer a few drops after moisturizer, while others find particular oils uncomfortable or unsuitable.",
          "Introduce oils carefully and pay attention to congestion, irritation, and how they behave with sunscreen or makeup.",
        ],
      },
    ],
    closing:
      "Choose products for their ingredients, instructions, and suitability—not only their category name—and seek professional guidance for persistent concerns.",
  },
  "when-to-seek-professional-skin-advice": {
    introduction:
      "Skincare should not require you to tolerate worsening pain, swelling, or persistent irritation. Knowing when to pause products is an important part of responsible personal care.",
    sections: [
      {
        heading: "Recognize concerning changes",
        paragraphs: [
          "Stop and reassess when a new product causes significant burning, swelling, blistering, widespread rash, or symptoms that continue to worsen. Severe swelling, breathing difficulty, or other urgent symptoms require immediate medical assistance.",
          "Persistent acne, pigment changes, infection signs, unusual growths, or recurring reactions deserve assessment rather than repeated product experimentation.",
        ],
      },
      {
        heading: "Do not try to treat every problem cosmetically",
        paragraphs: [
          "Beauty treatments and retail skincare have limits. A qualified provider should explain when a cosmetic service is unsuitable and when medical assessment is the safer next step.",
          "Avoid copying prescription routines or strong treatment combinations from another person. Similar-looking concerns can have different causes.",
        ],
      },
      {
        heading: "Prepare useful information",
        paragraphs: [
          "Record when symptoms started, the products and treatments used, relevant medication, allergies, and photographs of changes when appropriate. This history can help a qualified professional understand what happened.",
          "Do not conceal previous reactions because you want a particular service to proceed. Safety should take priority over completing an appointment.",
        ],
      },
    ],
    closing:
      "When you are uncertain, pause the suspected product and seek appropriate guidance. Prompt attention is better than continuing a routine that is making your skin worse.",
  },
};
