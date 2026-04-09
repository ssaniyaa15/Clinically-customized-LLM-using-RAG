/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AuditEntry } from '../models/AuditEntry';
import type { SaMDMetadata } from '../models/SaMDMetadata';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ComplianceService {
    /**
     * Get Audit Trail
     * @param offset
     * @param limit
     * @returns AuditEntry Successful Response
     * @throws ApiError
     */
    public static getAuditTrailComplianceAuditTrailGet(
        offset?: number,
        limit: number = 50,
    ): CancelablePromise<Array<AuditEntry>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/compliance/audit-trail',
            query: {
                'offset': offset,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Samd Metadata
     * @returns SaMDMetadata Successful Response
     * @throws ApiError
     */
    public static getSamdMetadataComplianceSamdMetadataGet(): CancelablePromise<SaMDMetadata> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/compliance/samd-metadata',
        });
    }
}
