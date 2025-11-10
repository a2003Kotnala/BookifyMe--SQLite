from flask import Blueprint, request
from app import db
from app.models.group import ReadingGroup, GroupMember
from app.utils.helpers import api_response, paginate_query
from app.utils.auth import jwt_required

community_bp = Blueprint('community', __name__)

@community_bp.route('/groups', methods=['GET'])
def get_groups():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '')
        
        # Base query
        query = ReadingGroup.query.filter_by(is_public=True)
        
        # Apply search filter
        if search:
            query = query.filter(ReadingGroup.name.ilike(f'%{search}%'))
        
        # Paginate results
        paginated_groups = paginate_query(query, page, per_page)
        
        return api_response({
            'groups': paginated_groups
        }, 'Groups retrieved successfully')
        
    except Exception as e:
        return api_response(None, 'Failed to fetch groups', 500, str(e))

@community_bp.route('/groups', methods=['POST'])
@jwt_required
def create_group(current_user):
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return api_response(None, 'Group name is required', 400)
        
        name = data.get('name').strip()
        description = data.get('description', '').strip()
        
        # Check if group name already exists
        if ReadingGroup.query.filter_by(name=name).first():
            return api_response(None, 'Group name already exists', 409)
        
        # Create new group
        group = ReadingGroup(
            name=name,
            description=description,
            created_by=current_user.id,
            is_public=data.get('is_public', True)
        )
        
        db.session.add(group)
        
        # Add creator as admin member
        member = GroupMember(
            group_id=group.id,
            user_id=current_user.id,
            role='admin'
        )
        db.session.add(member)
        
        db.session.commit()
        
        return api_response({
            'group': group.to_dict()
        }, 'Group created successfully', 201)
        
    except Exception as e:
        db.session.rollback()
        return api_response(None, 'Failed to create group', 500, str(e))

@community_bp.route('/groups/joined', methods=['GET'])
@jwt_required
def get_joined_groups(current_user):
    try:
        # Get groups where user is a member
        joined_groups = ReadingGroup.query.join(GroupMember).filter(
            GroupMember.user_id == current_user.id
        ).all()
        
        return api_response({
            'groups': [group.to_dict() for group in joined_groups]
        }, 'Joined groups retrieved successfully')
        
    except Exception as e:
        return api_response(None, 'Failed to fetch joined groups', 500, str(e))

@community_bp.route('/groups/<int:group_id>/join', methods=['POST'])
@jwt_required
def join_group(current_user, group_id):
    try:
        group = ReadingGroup.query.get(group_id)
        
        if not group:
            return api_response(None, 'Group not found', 404)
        
        # Check if already a member
        existing_member = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id
        ).first()
        
        if existing_member:
            return api_response(None, 'Already a member of this group', 409)
        
        # Add as member
        member = GroupMember(
            group_id=group_id,
            user_id=current_user.id,
            role='member'
        )
        
        db.session.add(member)
        db.session.commit()
        
        return api_response(None, 'Joined group successfully')
        
    except Exception as e:
        db.session.rollback()
        return api_response(None, 'Failed to join group', 500, str(e))

@community_bp.route('/groups/<int:group_id>/leave', methods=['POST'])
@jwt_required
def leave_group(current_user, group_id):
    try:
        # Find membership
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id
        ).first()
        
        if not membership:
            return api_response(None, 'Not a member of this group', 404)
        
        # Prevent group creator from leaving (or handle differently)
        if membership.role == 'admin':
            # Check if there are other admins
            other_admins = GroupMember.query.filter_by(
                group_id=group_id,
                role='admin'
            ).filter(GroupMember.user_id != current_user.id).first()
            
            if not other_admins:
                return api_response(None, 'Cannot leave as the only admin. Transfer ownership or delete group.', 400)
        
        db.session.delete(membership)
        db.session.commit()
        
        return api_response(None, 'Left group successfully')
        
    except Exception as e:
        db.session.rollback()
        return api_response(None, 'Failed to leave group', 500, str(e))

@community_bp.route('/groups/<int:group_id>', methods=['GET'])
def get_group_details(group_id):
    try:
        group = ReadingGroup.query.get(group_id)
        
        if not group:
            return api_response(None, 'Group not found', 404)
        
        # Get group members
        members = GroupMember.query.filter_by(group_id=group_id).all()
        
        group_data = group.to_dict()
        group_data['members'] = [member.to_dict() for member in members]
        
        return api_response({
            'group': group_data
        }, 'Group details retrieved successfully')
        
    except Exception as e:
        return api_response(None, 'Failed to fetch group details', 500, str(e))