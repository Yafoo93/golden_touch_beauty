"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { FormField, TextAreaField } from "@/components/ui/form-field";
import type { ServicePriceOption } from "@/lib/management-services";

type EditableOption = {
  name: string;
  description: string;
  price: string;
  duration_minutes: string;
};

function blankOption(): EditableOption {
  return { name: "", description: "", price: "", duration_minutes: "" };
}

export function ServicePriceOptionsEditor({
  initialOptions = [],
}: {
  initialOptions?: ServicePriceOption[];
}) {
  const [options, setOptions] = useState<EditableOption[]>(
    initialOptions.map((option) => ({
      name: option.name,
      description: option.description,
      price: option.price,
      duration_minutes: option.duration_minutes?.toString() ?? "",
    })),
  );

  function update(index: number, field: keyof EditableOption, value: string) {
    setOptions((current) =>
      current.map((option, optionIndex) =>
        optionIndex === index ? { ...option, [field]: value } : option,
      ),
    );
  }

  const submittedOptions = options.map((option, index) => ({
    name: option.name.trim(),
    description: option.description.trim(),
    price: option.price,
    duration_minutes: option.duration_minutes
      ? Number(option.duration_minutes)
      : null,
    display_order: index,
  }));

  return (
    <div className="service-price-options-editor management-form__wide">
      <input
        type="hidden"
        name="price_options"
        value={JSON.stringify(submittedOptions)}
      />
      <div className="service-price-options-editor__heading">
        <div>
          <h3>Option-based prices</h3>
          <p>
            Add named choices such as Standard, Premium, or Bridal Party. These
            are required only when Price options is selected above.
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="small"
          onClick={() => setOptions((current) => [...current, blankOption()])}
        >
          Add price option
        </Button>
      </div>
      {options.length ? (
        <div className="service-price-options-editor__list">
          {options.map((option, index) => (
            <section key={index}>
              <div className="service-price-options-editor__row">
                <FormField
                  name={`price-option-name-${index}`}
                  label="Option name"
                  value={option.name}
                  onChange={(event) => update(index, "name", event.target.value)}
                  maxLength={150}
                />
                <FormField
                  name={`price-option-price-${index}`}
                  label="Price (GHS)"
                  type="number"
                  value={option.price}
                  onChange={(event) => update(index, "price", event.target.value)}
                  min={0}
                  step="0.01"
                />
                <FormField
                  name={`price-option-duration-${index}`}
                  label="Duration (minutes)"
                  type="number"
                  value={option.duration_minutes}
                  onChange={(event) =>
                    update(index, "duration_minutes", event.target.value)
                  }
                  min={1}
                  max={1440}
                  hint="Optional override."
                />
              </div>
              <TextAreaField
                name={`price-option-description-${index}`}
                label="Option description"
                value={option.description}
                onChange={(event) =>
                  update(index, "description", event.target.value)
                }
                rows={2}
                maxLength={300}
              />
              <Button
                type="button"
                variant="outline"
                size="small"
                onClick={() =>
                  setOptions((current) =>
                    current.filter((_, optionIndex) => optionIndex !== index),
                  )
                }
              >
                Remove option
              </Button>
            </section>
          ))}
        </div>
      ) : (
        <p className="service-price-options-editor__empty">
          No structured price options added.
        </p>
      )}
    </div>
  );
}
