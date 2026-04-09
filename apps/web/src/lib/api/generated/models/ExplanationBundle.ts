/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GradCamOutput } from './GradCamOutput';
import type { LimeOutput } from './LimeOutput';
import type { ShapOutput } from './ShapOutput';
export type ExplanationBundle = {
    shap?: (ShapOutput | null);
    lime?: (LimeOutput | null);
    gradcam?: (GradCamOutput | null);
};

