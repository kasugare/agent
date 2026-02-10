#!/usr/bin/env python
# -*- code utf-8 -*-

from typing import Annotated, Dict, Optional, Any
from pydantic import BaseModel, ValidationError
from fastapi import Header, HTTPException


class HeaderModel(BaseModel):
    request_id: str
    session_id: str

class FileHeaderModel(BaseModel):
    x_sampl_job_id: str
    x_sampl_member_id: str
    x_sampl_callback: str
    x_sampl_err_callback: str
    x_sampl_user_data: str


async def get_headers(
        request_id: Annotated[str | None, Header(..., alias="request-id", convert_underscores=False)] = None,
        session_id: Annotated[str | None, Header(..., alias="session-id", convert_underscores=False)] = None,
) -> HeaderModel:
    try:
        if not request_id:
            raise HTTPException(status_code=400, detail="Missing required header: request_id")
        elif not session_id:
            raise HTTPException(status_code=400, detail="Missing required header: session_id")
        else:
            return HeaderModel(request_id=request_id, session_id=session_id)

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Invalid header format: {e.errors()}")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error while parsing headers: {str(e)}")


async def get_file_headers(
        x_sampl_job_id: Annotated[str, Header(..., alias="X-SAMPL-JOB-ID", convert_underscores=False)] = None,
        x_sampl_member_id: Annotated[str, Header(..., alias="X-SAMPL-MEMBER-ID", convert_underscores=False)] = None,
        x_sampl_callback: Annotated[str, Header(..., alias="X-SAMPL-CALLBACK", convert_underscores=False)] = None,
        x_sampl_err_callback: Annotated[
            str, Header(..., alias="X-SAMPL-ERR-CALLBACK", convert_underscores=False)] = None,
        x_sampl_user_data: Annotated[str, Header(..., alias="X-SAMPL-USER-DATA", convert_underscores=False)] = None,

) -> FileHeaderModel:
    try:
        if not x_sampl_job_id:
            raise HTTPException(status_code=400, detail="Missing required header: x_sampl_job_id")
        elif not x_sampl_member_id:
            raise HTTPException(status_code=400, detail="Missing required header: x_sampl_member_id")
        elif not x_sampl_callback:
            raise HTTPException(status_code=400, detail="Missing required header: x_sampl_callback")
        elif not x_sampl_err_callback:
            raise HTTPException(status_code=400, detail="Missing required header: x_sampl_err_callback")
        elif not x_sampl_user_data:
            raise HTTPException(status_code=400, detail="Missing required header: x_sampl_user_data")
        else:
            return FileHeaderModel(x_sampl_job_id=x_sampl_job_id, x_sampl_member_id=x_sampl_member_id,
                               x_sampl_callback=x_sampl_callback, x_sampl_err_callback=x_sampl_err_callback,
                               x_sampl_user_data=x_sampl_user_data)

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Invalid header format: {e.errors()}")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error while parsing headers: {str(e)}")

class StatusHeaderModel(BaseModel):
    x_sampl_job_id: str
    x_sampl_member_id: str

async def get_status_headers(
        x_sampl_job_id: Annotated[str, Header(..., alias="X-SAMPL-JOB-ID", convert_underscores=False)] = None,
        x_sampl_member_id: Annotated[str, Header(..., alias="X-SAMPL-MEMBER-ID", convert_underscores=False)] = None,

) -> StatusHeaderModel:
    try:
        if not x_sampl_job_id:
            raise HTTPException(status_code=400, detail="Missing required header: x_sampl_job_id")
        elif not x_sampl_member_id:
            raise HTTPException(status_code=400, detail="Missing required header: x_sampl_member_id")
        else:
            return StatusHeaderModel(x_sampl_job_id=x_sampl_job_id, x_sampl_member_id=x_sampl_member_id)

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Invalid header format: {e.errors()}")

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error while parsing headers: {str(e)}")
