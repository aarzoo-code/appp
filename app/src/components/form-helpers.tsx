import * as React from "react";
import { ControllerProps, FieldPath, FieldValues, useFormContext } from "react-hook-form";

type FormFieldContextValue<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> = {
  name: TName;
};

export const FormFieldContext = React.createContext<FormFieldContextValue>({} as FormFieldContextValue);

export type FormItemContextValue = {
  id: string;
};

export const FormItemContext = React.createContext<FormItemContextValue>({} as FormItemContextValue);

export const useFormField = <TFieldValues extends FieldValues = FieldValues>() => {
  const fieldContext = React.useContext(FormFieldContext as React.Context<FormFieldContextValue<TFieldValues>>);
  const itemContext = React.useContext(FormItemContext);
  const { getFieldState, formState } = useFormContext<TFieldValues>();

  const fieldState = getFieldState(fieldContext.name as FieldPath<TFieldValues>, formState);

  if (!fieldContext) {
    throw new Error("useFormField should be used within <FormField>");
  }

  const { id } = itemContext;

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    ...fieldState,
  };
};

export {};
